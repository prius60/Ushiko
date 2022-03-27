import validators
from youtube_search import YoutubeSearch
import discord
import youtube_dl
import bilibili_api
from bilibili_api import misc
import ssl


ssl._create_default_https_context = ssl._create_unverified_context


async def get_url(keyword, source: str = 'YouTube') -> str:
    """Returns a media link from user's keyword, by either straight returning it
    or looking up one from keywords.

    <get_url> searches media within youtube, if <source> is unspecified
    """
    if validators.url(keyword):
        return keyword
    if source.lower() == 'youtube' or source.lower() == 'utube':
        r = YoutubeSearch(keyword, max_results=1).to_dict()[0]['url_suffix']
        return f'https://youtube.com{r}'
    elif source.lower() == 'bili' or source.lower() == 'bilibili':
        result = await misc.web_search_by_type(keyword, 'video')
        return result['result'][0]['arcurl']
    else:
        # TODO: add support for additional websites
        raise NotImplementedError


def get_keyword(*args) -> (str, str):
    source = 'YouTube'
    if len(args) == 0 or args[0] is None:
        return '', source
    args = list(args)
    if not len(args) == 1:
        if args[len(args) - 1].lower() == 'bili' or args[len(args) - 1].lower() == 'bilibili':
            args.pop()
            source = 'BiliBili'
        elif args[len(args) - 1].lower() == 'youtube' or args[len(args) - 1].lower() == 'utube':
            args.pop()
    if len(args) == 0:
        return '', source
    keyword = ' '.join(args)
    return keyword, source


def get_audio_YouTube(url: str) -> discord.FFmpegOpusAudio:
    """Return an Opus audio from YouTube <url> provided

    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '192',
        }]
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.cache.remove()
        info = ydl.extract_info(url, download=False)
    url = info['formats'][0]['url']
    ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1'
                                     ' -reconnect_delay_max 5',
                   'options': '-vn'}
    return discord.FFmpegOpusAudio(url, **ffmpeg_opts)


def get_audio_Bili(url: str) -> discord.FFmpegPCMAudio:
    """Return an PCM audio from Bilibili <url> provided

    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '192',
        }]
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    url = info['formats'][0]['url']
    ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1'
                                     ' -reconnect_delay_max 5',
                   'options': '-vn'}
    return discord.FFmpegPCMAudio(url, **ffmpeg_opts)
