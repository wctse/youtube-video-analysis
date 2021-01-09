# TODO: Incorporate the scrape time into the processes

import pandas as pd
import scraping
import json
from datetime import datetime

key = open('api-key.txt', 'r').read()
now = datetime.now().strftime('%Y%m%d_%H%M%S')
now_dt = datetime.strptime(now, '%Y%m%d_%H%M%S')
old_csv = 'data/csv/data_20210109_153153.csv'  # Change this

# Find channels to scrape videos on
if input('Type "yes" if you wish to scrape channel ids.').lower() == 'yes':
    channels = ['UCYO_jab_esuFRV4b17AJtAw']
    if key == 'Insert your API key here':
        print('Please edit api-key.txt to your own API key.')
    else:
        channels += scraping.scrape_channel_ids(['UCYO_jab_esuFRV4b17AJtAw'], depth=6, write_to_file=True)

# Scrape videos
# with open('data/channels/channels_' + now + '.txt', 'r') as file:
with open('data/channels/channels_20201229_182240.txt', 'r') as file:
    channels = file.read().splitlines()

videos, scrape_time = scraping.get_video_from_channels(key, channels[3600:4400],
                                                       how_many_videos=10, subscriber_threshold=1000)

with open('data/raw/' + now + '.json', 'a') as file:
    json.dump(videos, file)

# Use option 1 for live processing, option 2 for delayed processing
## Option 1
with open('data/raw/' + now + '.json', 'r', encoding='utf-8') as file:
    raw = json.load(file)

## Option 2
# with open('data/raw/20201231_133112.json', 'r') as file:
#     raw = json.load(file)

# Parse video formats and output into a csv
parsed = scraping.parse_video_details(raw, now_dt)
df = pd.DataFrame(parsed)

# Combine new csv with old csv
df_old = pd.read_csv(old_csv, index_col=0)
df_concat = pd.concat([df_old, df]).reset_index()
df_concat.to_csv('data/csv/data_' + now + '.csv')
