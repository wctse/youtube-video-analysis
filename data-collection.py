import pandas as pd
from googleapiclient.discovery import build
from scraping import get_video_from_channel, scrape_channel_id

from datetime import datetime

key = open('api-key.txt', 'r').read()

if key == 'Insert your API key here':
    print('Please edit api-key.txt to your own API key.')
else:
    youtube = build('youtube', 'v3', developerKey=key)
    channels = scrape_channel_id(['UCYO_jab_esuFRV4b17AJtAw'], depth=1)
    channels.to_csv('data_' + datetime.now().strftime('%Y%m%d%H%M'))