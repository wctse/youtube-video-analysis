# Youtube Video Analyis: Project Overview
This project is an analysis on what contributes to the popularity (or unpopularity) of a YouTube video, except from its content and the consequent average time viewed by each viewer. In the project we explore different opportunities to make your video stand out and improve viewership on top of your creativity, to harness the algorithm.

## Resources (will be) Used
#### Packages
* numpy
* pandas
* selenium
* Google API
* scikit-learn
* tensorflow
* opencv, imageAI (YOLO)

#### Other Resources
* Font "A Big Deal": https://www.dafont.com/a-big-deal.font
* Pre-trained YOLO model: From https://stackabuse.com/object-detection-with-imageai-in-python/

## Project Status
This project is currently in development. Users are now able to:
* Automatically find users to scrape by the "Channels" page on each YouTube channel
* Scrape the title and thumbnail of a certain amonut of recent videos

These sections or features are to be developed:
* Explore the nature of the data
* Generate quantitative data from the titles and thumbnails
* Apply ordinary models and neural network onto the data and analyse the findings

## Motivation
One of the main motivation to creating this project is this Veritasium (A popular scientific YouTube channel) video:

[![My Video Went Viral. Here's Why](https://i.ytimg.com/vi/fHsa9DqmId8/hq720.jpg?sqp=-oaymwEZCNAFEJQDSFXyq4qpAwsIARUAAIhCGAFwAQ==&rs=AOn4CLBme2X0lAIEWCgphf9-k3IqGtnT9w)](https://www.youtube.com/watch?v=fHsa9DqmId8)

This video pointed out the nature of how YouTube shows video to people: Based on their, and other people's preferences, that is judged by the data on what video they click into.

Therefore, if we are possible to find the trick, or at least tips on what kind of title or thumbnail would perform the best in this vehement competition, those people may be able to gain an unfair competitive advantage without even improving their ocntent.

#### Who should explore this
* YouTubers
* Marketers
* Pepole who are interested in the usage of NLP and Image Recognition
* General data science enthusiasts

## General Walk-through
#### Scraping
The difficulty on scraping videos lies on the below two problems:
1. Finding the suitable channel to scrape their videos
2. Finding the suitable video to gather data

The second problem contributes to the first. The measure of "popularity" of a video cannot be simply the number of views, because by nature different kinds of video have a different viewer base. For example, music videos are generally much more viewed than others. Among the top 10 videos, 8 of them are music videos. (If you are curious, they are Despacito, Shape of You, See You Again, Uptown Funk, Sorry, Sugar and Roar.)

To add on that, YouTube biases video pushing to a channel's subscribers. It is trivial that if you subscribe to a channel the algorithm will try to push more of its contents to you, more so if you enable the 'bell'. Therefore, we here roughly define the popularity as:

<p style="text-align: center;"><img src="https://render.githubusercontent.com/render/math?math=\displaystyle\text{Popularity}=\frac{\text{Views of the Video}}{\text{Subscribers of the Channel}}"></p>

\
Then the problem lies on how to find the suitable channels to scrape from. Luckily there is usually a "Channels" page of each YouTube channel, like the following:
![Vsauce: Channels](https://i.imgur.com/xDauW5D.png)

Sometimes they suggest relevent channels to viewers because of collaborations, or they simply want to introduce a good channel to their subscribers. No matter why, we can easily use this feature to theortically find unlimited channels to scrape from.

### Removing Certain Types of Videos

## Guides
#### Scraping
The code demands a plain text file "api-key.txt" to identify and authenticate the Google API. Simply copy and paste the key generated by Google into the text file without adding any other contents.

## Results
