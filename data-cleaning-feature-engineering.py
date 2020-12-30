import pandas as pd

import re
import requests
from datetime import timedelta

key = open('api-key.txt', 'r').read()
df = pd.read_csv('data/csv/data_20201230_194925.csv', index_col=0)

# (1) Filter data that is not English-based, or consists of English localizations

# (2) Column: 'published_at'
df['published_at'] = pd.to_datetime(df['published_at'])

## Remove videos that are published in the latest 48 hours as views may have not been accumulated
df = df[df['published_at'] < df['published_at'].max() - timedelta(hours=48)]

## Binning into different hours of publishing
df['hour_published'] = df['published_at'].apply(lambda x: x.hour)
df['hour_published'] = pd.cut(df['hour_published'], bins=8, right=False, labels=['0-2', '3-5', '6-8', '9-11',
                                                                                 '12-14', '15-17', '18-20', '21-23'])


# (2) Column: 'length'
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

# (3) Column: 'category'
categories = {}

## Request the list of categories from YouTube.
## It occasionally updates so it is important to run this shortly after scraping.
url = f"https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&regionCode=HK&key={key}"
response = requests.request('GET', url).json()

for i in response['items']:
    categories[i['id']] = i['snippet']['title']

df['category'] = df['category'].apply(str).map(categories)

# Filter out music videos because the viewership nature is different from other types of videos
df = df[df['category'] != 'Music']

# (4) Column: 'title'
## Length
df['title_length'] = df['title'].apply(len)
## Capital Letters
## Sentiment Analysis, untreated & absolute
## What word does the title start with?

# (5) Column: 'thumbnail'
## Dominant Colour
## Are there people?
## Are there animals?
## Are there squares, boxes, circles that highlights things?
## Are there words?
