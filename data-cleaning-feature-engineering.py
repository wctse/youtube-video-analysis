import numpy as np
import pandas as pd
import re
import requests
from datetime import datetime, timedelta

now = datetime.now().strftime('%Y%m%d_%H%M%S')
key = open('api-key.txt', 'r').read()
csv = 'data_20210101_145809.csv'
df = pd.read_csv(f'data/csv/{csv}', index_col=0)

# (1) Filter data
## 1a. Videos that is not English-based, or consists of English localizations
## 1b. Videos that are live streams
df = df[df['live'] == 0]

# (2) Column: 'published_at'
df['published_at'] = pd.to_datetime(df['published_at'])

## 2a. Remove videos that are published in the latest 48 hours as views may have not been accumulated
df = df[df['published_at'] < df['published_at'].max() - timedelta(hours=48)]

## 2b. Binning into different hours of publishing
df['hour_published'] = df['published_at'].apply(lambda x: x.hour)
df['hour_published'] = pd.cut(df['hour_published'], bins=8, right=False, labels=['0-2', '3-5', '6-8', '9-11',
                                                                                 '12-14', '15-17', '18-20', '21-23'])


# (3) Column: 'length'
def length_parse(length):
    """
    The original format for length from retrieved data is "PT__H__M__S",
    with H for hours, M for minutes and S for seconds.
    This function converts it to pure seconds.
    """
    length = re.split('[HM]', length[2:-1])
    if len(length) == 3:
        length = int(length[0]) * 3600 + int(length[1]) * 60 + int(length[2])
    elif len(length) == 2:
        length = int(length[0]) * 60 + int(length[1])
    else:
        length = int(length[0])
    return length


df['length'] = df['length'].apply(length_parse)

# (4) Column: 'category'
categories = {}

## 4a. Request the list of categories from YouTube.
## 4b. It occasionally updates so it is important to run this shortly after scraping.
url = f"https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&regionCode=HK&key={key}"
response = requests.request('GET', url).json()

for i in response['items']:
    categories[i['id']] = i['snippet']['title']

df['category'] = df['category'].apply(str).map(categories)

# 4c. Filter out music videos because the viewership nature is different from other types of videos
df = df[df['category'] != 'Music']

# (5) Column: 'title'

## 5a. Length
df['title_length'] = df['title'].apply(len)

## 5b. Are there any all-capital words?
df['any_capitalized_word'] = np.nan

titles_tokenized = list(df['title'].apply(str.split))

for i, title in enumerate(titles_tokenized):
    df.iat[i, df.columns.get_loc('any_capitalized_word')] =\
        any([True if word == word.upper() else False for word in title])

## 5c. Is the whole title capitalized?
df['all_capitalized_word'] = df['title'].apply(lambda x: 1 if x == x.upper() else 0)

## 5d. Sentiment Analysis, untreated & absolute
## 5e. What word does the title start with?

# (6) Column: 'thumbnail'
## 6a. Dominant Colour
## 6b. Are there people?
## 6c. Are there animals?
## 6d. Are there squares, boxes, circles that highlights things?
## 6e. Are there words?

# (7) Column: 'length'
df['length=10m+'] = df['length'].apply(lambda x: 1 if x > 600 else 0)

df.to_csv('data/cleaned_csv/data_' + now + '_cleaned.csv')