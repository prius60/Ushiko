# Ushiko
A simple discord bot for audio stream

## Features
- Playing audio stream from YouTube
- Playing audio stream from Bilibili
- Searching media by keywords
- Queued playback

## Requirements
- Python 3.8+
- ffmpeg
- Packages required in Requirements.txt, which can be installed with <b>pip install \<package name\></b>

## Sample usage
Commands should be typed into a bot-accessible chat, with no prefixes
- To play audio from YouTube, use: <b>play \<keyword\></b> or <b>play \<link\></b>
- To play audio from BiliBili, use: <b>play \<keyword\> bili</b> or <b>play \<link\></b>
- To add to queue, simply do the same above and the media will be queued

## Motivation
This project was not created as a professional production discord bot at the very beginning. Rather, it a personal project intended for messing around with my friends in our private discord. :)  

Implementation of its features is rather primitive. For example, media/metadata fetching was not through YouTube's official data API, but through third-party modules such as youtube-search and bilibili_api. I was able to achieve simple audio streaming with the help of ffmpeg at the end, but it doesn't change the fact that Ushiko performs unstable due to third-party modules fetching no feedback from the media providers.

