from pandas import DataFrame
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from datetime import datetime
from time import sleep
from tqdm import tqdm


def scrape_channel_ids(initial_channelIds: list, depth: int, checkpoint_at: int = 0, write_to_file: bool = True):
    """
    The function to scrape the ID of other channels for scraping. Utilises the "channels" page of each channel on
    YouTube.

    :param initial_channelIds: The channels to start with.
    :param depth: How many layers of "channels" to search for, starting from the initial channel.
    :param checkpoint_at: Default 0. If positive, record the intermediate results in the designated txt file.
    :param write_to_file: Default true. If true, directly write the results to the data folder
    :return: A list of channel IDs.

    TODO:
    * Solve the bug where the list of channels returned include non-ids (names of channel only) but ends with the
      word "channel"
    """

    options = ChromeOptions().add_experimental_option('prefs', {
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
    })

    initial_channels = ['https://www.youtube.com/channel/' + channelIds for channelIds in initial_channelIds]

    # Intermediate channels for processing in the loop
    intermediate_channels = [] + initial_channels

    # Processed channels to document the channels processed, to prevent duplicated retrieval
    processed_channels = [] + initial_channels

    # Result channels for function return
    result_channels = [] + initial_channelIds

    driver = webdriver.Chrome('chromedriver.exe', chrome_options=options)
    sleep(3)

    count = 0

    for i in tqdm(range(depth)):

        print('Iteration ' + str(i) + '...')
        for channel in intermediate_channels.copy():
            processed_channels += [channel]

            # Navigate to the "channels" page of the YouTube channel
            driver.get(channel + '/channels')

            # Identify all linked channels
            elements = driver.find_elements_by_id('channel-info')
            links = [elem.get_attribute('href') for elem in elements]

            intermediate_channels += [x for x in links if x not in processed_channels]

            result_channels += [x[32:] for x in links if ('channel/UC' in x and x not in processed_channels)]
            intermediate_channels.remove(channel)

            count += 1
            if count == checkpoint_at:
                count = 0
                with open('data/channels/checkpoints/checkpoint_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.txt',
                          'a') as file:
                    file.write('\n'.join(result_channels))

    driver.close()

    if write_to_file:
        with open('data/channels/channels_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.txt', 'a') as file:
            file.write('\n'.join(result_channels))

    return result_channels


def get_video_from_channels(api_key: str, channelIds: list, how_many_videos: int, subscriber_threshold: int = 1000):
    """
    The function to get video det   ails from the channel. It contains the raw returns from Google API. Note that certain
    limits on the maximum video scraped daily is imposed by Google, and the function automatically returns the scraped
    videos if it is terminated by Google.

    This function takes advantage of an automatic playlist generation by YouTube that, any channel IDs would have an
    initial of "UC" and its playlist can be retrieved by changing the initial of "UU". Then the function requests
    the video information from Google API.

    :param api_key: The api key used for the Google API.
    :param channelIds: The channel to scrape video from.
    :param how_many_videos: The limit to the amount of videos to scrape from a channel.
    :param subscriber_threshold: The minimum subscriber needed for a channel's video to be scraped.
    :return: A list of video contents from the given channels.

    TODO:
    * Add metadata on when the videos are scraped.
    """

    if subscriber_threshold < 1:
        raise ValueError('Subscriber threshold should not be smaller than 1')

    if how_many_videos < 1:
        raise ValueError('Video number per channel should not be smaller than 1')

    youtube = build('youtube', 'v3', developerKey=api_key)

    video_details = []  # Variable for tracking videos in each channel
    count = 0  # Variable for how many videos scraped

    # Variables to track these situations and report at the end of the function:
    not_exist = []  # Not existing channels
    no_video = [] # No video
    disabled_sub = [] # Disabled function to check the number of subscribers
    video_id = ''

    try:
        for channel in tqdm(channelIds):

            # Gather statistics of the channel
            channel_stat = youtube.channels().list(id=channel, part=['statistics']).execute()

            if not channel_stat['pageInfo']['totalResults']:
                not_exist += [channel]
                continue

            try:
                sub = int(channel_stat['items'][0]['statistics']['subscriberCount'])
            except KeyError:
                disabled_sub += [channel]
                continue

            # Skip the channel if it has subscriber count less than the threshold
            if sub < subscriber_threshold:
                continue

            # Use the channel id to retrieve the playlist id, which contains all uploads by that channel
            playlist_id = channel[0] + 'U' + channel[2:]

            # Retrieve the id of reach video
            try:
                channel_videos = youtube.playlistItems().list(playlistId=playlist_id,
                                                              part=['snippet'],
                                                              maxResults=how_many_videos).execute()
            # Case where the channel does not have any videos, so the API returns HttpError "cannot be found"
            except HttpError:
                no_video += [channel]
                continue

            video_ids = [video['snippet']['resourceId']['videoId'] for video in channel_videos['items']]

            # Retrieve the detailed information of each video
            for video_id in video_ids:
                detail = youtube.videos().list(id=video_id,
                                               part=['id', 'snippet', 'statistics', 'contentDetails', 'topicDetails',
                                                     'recordingDetails', 'liveStreamingDetails', 'localizations'],
                                               maxResults=1).execute()['items'][0]
                detail['channel_subscribers'] = sub
                video_details += [detail]
                count += 1

    # Stop the process and return the existing results when API limit is reached
    except HttpError:
        print(f'YouTube API blocked the request upon request information for video with ID {video_id}.\n' +
              'Possibly API Request limit exceeded.\n' +
              f'Returning requested data for the scraped {count} videos.')

    # Notify the user on non-existing channels
    if not_exist:
        print(f'Channel(s) with the following id do not exist:')
        for channel in not_exist:
            print(channel)

    if no_video:
        print(f'Channel(s) with the following id do not have videos:')
        for channel in no_video:
            print(channel)

    print(f'Scraped the details of {count} videos.')

    return video_details


def parse_video_details(video_details: dict):
    info = {}

    for d in video_details:
        video_id = d['id']

        sub = d.get('channel_subscribers')
        view = int(d.get('statistics').get('viewCount'))

        # Choose certain useful information and append into a list
        info[video_id] = ({
            'title': d.get('snippet').get('title'),
            'view': view,
            'channel_sub': sub,
            'view_to_sub': view / sub,
            'like': d.get('statistics').get('likeCount'),
            'dislike': d.get('statistics').get('dislikeCount'),
            'comment': d.get('statistics').get('commentCount'),
            'length': d.get('contentDetails').get('duration'),
            'description': d.get('snippet').get('description'),
            'dimension': d.get('contentDetails').get('dimension'),
            'definition': d.get('contentDetails').get('definition'),
            'caption': d.get('contentDetails').get('caption'),
            'published_at': d.get('snippet').get('publishedAt'),
            'tags': d.get('snippet').get('tags'),
            'category': d.get('snippet').get('categoryId'),
            'thumbnail': d.get('snippet').get('thumbnails').get('high').get('url'),
        })

        try:
            info[video_id]['localizations'] = d.get('localizations').keys()
        except AttributeError:
            info[video_id]['localizations'] = ''

        try:
            info[video_id]['topic_categories'] = d.get('topicDetails').get('topicCategories')
        except AttributeError:
            info[video_id]['topic_categories'] = ''

        try:
            info[video_id]['default_language'] = d.get('snippet').get('defaultLanguage')
        except AttributeError:
            info[video_id]['default_language'] = ''

    info = DataFrame(info).transpose()

    return info
