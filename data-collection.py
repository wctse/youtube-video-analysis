import pandas as pd
from scraping import get_video_from_channel, scrape_channel_id
from datetime import datetime

key = open('api-key.txt', 'r').read()
channels = ['UCYO_jab_esuFRV4b17AJtAw']

if key == 'Insert your API key here':
    print('Please edit api-key.txt to your own API key.')
else:
    channels += scrape_channel_id(['UCYO_jab_esuFRV4b17AJtAw'], depth=1)
    videos = get_video_from_channel(key, channels, 5, 1000)
    pd.DataFrame(videos).to_csv('data/data_' + datetime.now().strftime('%Y%m%d%H%M') + '.csv')