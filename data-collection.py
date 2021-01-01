# TODO: Incorporate the scrape time into the processes

import pandas as pd
import scraping
import json
from datetime import datetime

# import importlib
# importlib.reload(scraping)

key = open('api-key.txt', 'r').read()
channels = ['UCYO_jab_esuFRV4b17AJtAw']
now = datetime.now().strftime('%Y%m%d_%H%M%S')


# Find channels to scrape videos on
if key == 'Insert your API key here':
    print('Please edit api-key.txt to your own API key.')
else:
    channels += scraping.scrape_channel_ids(['UCYO_jab_esuFRV4b17AJtAw'], depth=6, write_to_file=True)

# Scrape videos
# with open('data/channels/channels_' + now + '.txt', 'r') as file:
with open('data/channels/channels_20201229_182240.txt', 'r') as file:
    channels = file.read().splitlines()

videos, scrape_time = scraping.get_video_from_channels(key, channels, how_many_videos=1, subscriber_threshold=1000)

with open('data/raw/' + now + '.json', 'a') as file:
    json.dump(videos, file)

# Use option 1 for live processing, option 2 for delayed processing
## Option 1
with open('data/raw/' + now + '.json', 'r') as file:
    raw = json.load(file)

## Option 2
with open('data/raw/20201231_133112.json', 'r') as file:
    raw = json.load(file)

# Parse video formats and output into a csv
parsed = scraping.parse_video_details(raw, _)
pd.DataFrame(parsed).to_csv('data/csv/data_' + now + '.csv')