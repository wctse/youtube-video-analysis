from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ChromeOptions
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pandas import DataFrame

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ChromeOptions
from datetime import datetime
from time import sleep

from tqdm import tqdm


def get_video_from_channel(api_key: str, channelIds: list, how_many_videos: int, subscriber_threshold: int = 1000):

    if subscriber_threshold < 1:
        raise ValueError('Subscriber threshold should not be smaller than 1')

    if how_many_videos < 1:
        raise ValueError('Video number per channel should not be smaller than 1')

    youtube = build('youtube', 'v3', developerKey=api_key)

    channels_videos = []
    insufficient_videos = {}

    try:
        for count, channel in tqdm(enumerate(channelIds)):
            channel_stat = youtube.channels().list(part=['statistics'], id=channel).execute()

            if not channel_stat['pageInfo']['resultsPerPage']:
                print(f'Channel with id {channel} does not exist.')
                continue

            sub = int(channel_stat['items'][0]['statistics']['subscriberCount'])

            if sub < subscriber_threshold:
                continue

            playlistId = channel[0] + 'U' + channel[2:]

            videos = youtube.playlistItems().list(playlistId=playlistId, part=['id, snippet'],
                                                  maxResults=how_many_videos).execute()

            try:
                for i in range(how_many_videos):
                    try:
                        video_id = videos['items'][i]['snippet']['resourceId']['videoId']
                        video_detail = youtube.videos().list(id=video_id, part='statistics').execute()

                        channels_videos.append({
                            'title': videos['items'][i]['snippet']['title'],
                            'thumbnail': videos['items'][i]['snippet']['thumbnails']['high']['url'],
                            'view_to_sub': int(video_detail['items'][0]['statistics']['viewCount']) / sub,
                            'channel_sub': sub,
                            'published_at': videos['items'][i]['snippet']['publishedAt'],
                        })

                    # In some occasions the dictionary items do not exist in request results
                    except KeyError:
                        continue

            # When there are not enough videos for a channel (smaller than how_many_videos),
            # Record the channel id to report at the end of the function
            except IndexError:
                insufficient_videos[channel] = i+1
                continue

    # Stop the process and return the existing results when API limit is reached
    except HttpError:
        print(f'API Request limit exceeded. Returning requested data for the first {count} channels.')

    if insufficient_videos:
        print('Channels with insufficient videos:')
        for (key, value) in insufficient_videos.items():
            print(f'Channel {key} only contains {value} video(s).')

    return channels_videos


def chain_scrape_channel_id(initial_channelIds: list, depth: int = 3, checkpoint_at: int = 100):

    options = ChromeOptions().add_experimental_option('prefs', {
    'download.prompt_for_download': False,
    'download.directory_upgrade': True,
    })

    initial_channels = ['https://www.youtube.com/channel/' + channelIds for channelIds in initial_channelIds]

    intermediate_channels = [] + initial_channels
    processed_channels = [] + initial_channels
    result_channels = [] + initial_channelIds

    driver = webdriver.Chrome('chromedriver.exe', chrome_options=options)
    sleep(3)

    counter = 0

    for i in tqdm(range(depth)):

        print('Iteration ' + str(i) + '...')
        for channel in tqdm(intermediate_channels.copy()):
            processed_channels += [channel]

            driver.get(channel + '/channels')

            elements = driver.find_elements_by_id('channel-info')
            links = [elem.get_attribute('href') for elem in elements]

            intermediate_channels += [x for x in links if x not in processed_channels]

            result_channels += [x[32:] for x in links if ('channel/UC' in x and x not in processed_channels)]
            intermediate_channels.remove(channel)

            counter += 1
            if counter == checkpoint_at:
                counter = 0
                f = open('checkpoints/checkpoint_' + datetime.now().strftime('%Y%m%d%H%M') + '.txt', 'a')
                f.write('\n'.join(result_channels))
                f.close()

    driver.close()

    return result_channels
