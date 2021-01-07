"""
This .py file runs on TensorFlow 1.15.
Any TensorFlow 2 version would return error in part 6 regarding object detection.
It is suggested for users to create an extra environment explicitly with TF 1.15.
"""

import numpy as np
import pandas as pd
from google.cloud import storage, vision
from google.cloud import translate_v2 as translate

import re
import requests
from datetime import datetime, timedelta
from tqdm import tqdm

# Turn off "A value is trying to be set on a copy of a slice from a DataFrame" warning
pd.options.mode.chained_assignment = None

now = datetime.now().strftime('%Y%m%d_%H%M%S')
key = open('api-key.txt', 'r').read()
csv = 'data_20210106_220013.csv'  # Change this
df = pd.read_csv(f'data/csv/{csv}', index_col=0)

# (1) Filter data
## 1a. Videos that is not English-based, or consists of English localizations

# There are multiple versions of English in YouTube Database, change all of them into 'en'
english = ['en', 'en-GB', 'en-US', 'en-CA']
df['language'] = df.default_language.apply(lambda x: 'en' if x in english else x)

# Find out those without data about their language and scan their titles through Google Cloud Translate API
df_languageless = df.copy()
df_languageless = df_languageless[df_languageless.default_language.isna()]
df_languageless = df_languageless

translate_client = translate.Client()
title_languages = translate_client.detect_language(list(df_languageless.title))

# Record the languages if the confidence is over 0.9
df_languageless['language'] = [d['language'] if d['confidence'] > 0.9
                               else None for d in title_languages]

# Filter out those with confidence lower than 0.9
df_languageless_still = df_languageless.copy()
df_languageless_still = df_languageless_still[df_languageless_still.language.isna()]

# Scan the descriptions of videos that is still unidentified
if len(df_languageless_still) > 0:
    descriptions = df_languageless_still.description
    descriptions = descriptions.fillna('')
    descriptions = list(descriptions)

    description_languages = translate_client.detect_language(descriptions)
    df_languageless_still['language'] = [d['language'] if d['confidence'] > 0.9
                                         else None for d in description_languages]

# Only select instances that are identified as English
df = pd.concat([df[df['language'] == 'en'],
                df_languageless[df_languageless['language'] == 'en'],
                df_languageless_still[df_languageless_still['language'] == 'en']])

## 1b. Filter videos that are live streams
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
# TODO: Rearrange the columns after running all thumbnails through Google Vision API

## 6a. Dominant Colour


## 6b & 6c
## Google Vision API is used in this section.
## It is also required to set the Environment Variable "GOOGLE_APPLICATION_CREDENTIALS" to a json file provided by
## Google. Check https://cloud.google.com/docs/authentication/getting-started for more details.

## Explicitly use service account credentials by specifying the private key file.
storage_client = storage.Client.from_service_account_json('google-cloud/service-account.json')

annotator = vision.ImageAnnotatorClient()
image = vision.Image()

df['thumbnail_objects'] = 0
df['thumbnail_text_length'] = 0
df['thumbnail_text_content'] = None
max_text_length = 0

for i, url in tqdm(enumerate(df['thumbnail'])):
    image.source.image_uri = url

    ## 6b. Object Detection

    objects = annotator.object_localization(image=image).localized_object_annotations
    df.iloc[i, df.columns.get_loc('thumbnail_objects')] = len(objects)

    for object_ in objects:
        column_name = 'thumbnail_' + object_.name.replace(' ', '').lower()
        if column_name not in df.columns:
            df[column_name] = 0
        if object_.score > 0.5:
            df.iloc[i, df.columns.get_loc(column_name)] += 1

    ## 6c. Are there words? What are they?
    ## TODO: Some OCR-recognized texts are not words, and they should be separated from clear words
    ##  on the thumbnail in feature generation.

    texts = annotator.text_detection(image=image).text_annotations

    # Only assign values to DataFrame if there are texts
    if texts:
        text_lines = texts[0].description.split('\n')[:-1]

        # Create new columns in df if the length of the list is longer than the number of existing columns
        if max_text_length < len(text_lines):
            for x in range(max_text_length, len(text_lines)):
                df['thumbnail_text_' + str(x)] = None
            max_text_length = len(text_lines)

        for x, text in enumerate(text_lines):
            df.iloc[i, df.columns.get_loc('thumbnail_text_' + str(x))] = text

        df.iloc[i, df.columns.get_loc('thumbnail_text_length')] = len(text_lines)

    ## 6d. Are there squares, boxes, circles that highlights things?

df.to_csv('data/cleaned_csv/data_' + now + '_cleaned.csv')