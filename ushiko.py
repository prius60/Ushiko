import os

import discord
from discord.ext import commands
import media_fetcher
import media_queue
import asyncio
import youtube_dl
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
intents = discord.Intents.all()
ushiko = commands.Bot(command_prefix='', intents=intents)
queue_dict = {}


# queue = media_queue.Queue()


@ushiko.event
async def on_ready():
    """Welcome info.

    """
    print('Logged in as')
    print(ushiko.user.name)
    print(ushiko.user.id)
    print('------')


@ushiko.command(aliases=['来'])
async def summon(ctx):
    """Join the user's voice channel

    """
    destination = ctx.author.voice.channel
    await destination.connect()


@ushiko.command(aliases=['滚'])
async def dismiss(ctx):
    """Dismiss Ushiko

    """
    for x in ushiko.voice_clients:
        if x.channel == ctx.author.voice.channel:
            if x.channel in queue_dict:
                queue_dict.pop(x.channel)
            await ctx.send(':pleading_face:')
            await x.disconnect(force=True)
            return


@ushiko.command(aliases=['整活', '播放', '继续'])
async def play(ctx, *args):
    """Play audio from the provided source and keyword. Supports media from YouTube
    and BiliBili

    """
    channel = ctx.author.voice.channel
    if channel in queue_dict:
        queue = queue_dict[channel]
    else:
        queue_dict[channel] = media_queue.Queue()
        queue = queue_dict[channel]
    if len(args) == 0:
        if queue.is_paused:
            for x in ushiko.voice_clients:
                if x.channel == ctx.author.voice.channel:
                    x.resume()
                    queue.is_paused = False
                    return
        elif queue.is_empty():
            await ctx.send(':x: **   Provide a link or search with keywords**')
    else:
        keyword, source = media_fetcher.get_keyword(*args)
        url = await media_fetcher.get_url(keyword, source)
        if queue.is_looping and (queue.current_song == "" or url == queue.current_song):
            queue.enqueue_with_priority(url)
        else:
            queue.enqueue(url)

    voice = discord.utils.get(ushiko.voice_clients, guild=ctx.guild)
    if voice is None or not voice.is_playing():
        url = queue.dequeue()
        connected = False
        for client in ushiko.voice_clients:
            if client.channel == ctx.author.voice.channel:
                connected = True
        if not connected:
            await summon(ctx)
            print('Ushiko is now connected to users voice channel')
        voice = discord.utils.get(ushiko.voice_clients, guild=ctx.guild)
        if 'youtu' in url:
            voice.play(media_fetcher.get_audio_YouTube(url),
                       after=lambda e: asyncio.run_coroutine_threadsafe(skip(ctx), ushiko.loop))
            print('Ushiko is now playing media from YouTube')
        else:
            try:
                voice.play(media_fetcher.get_audio_Bili(url),
                           after=lambda e: asyncio.run_coroutine_threadsafe(skip(ctx), ushiko.loop))
                print('Ushiko is now playing media from BiliBili')
            except youtube_dl.utils.DownloadError:
                await ctx.send(':x: **   Media source unsupported**')
        if voice.is_playing() and not queue.is_looping:
            await ctx.send(f'**Now playing: **' + f'{url}')
            print(f'Playing {url}')
    else:
        print(f'Added to playlist: {url}')
        await ctx.send(f'**Added to playlist: **{url}')


@ushiko.command(aliases=['洗脑', '循环'])
async def loop(ctx):
    """Loop the current song

    """
    channel = ctx.author.voice.channel
    if channel in queue_dict:
        queue = queue_dict[channel]
    else:
        return
    if not queue.is_looping:
        queue.is_looping = True
        await ctx.send("**Now looping**")
    else:
        queue.is_looping = False
        await ctx.send("**Looping is now off**")


@ushiko.command(aliases=['歌单', '播放列表'])
async def playlist(ctx):
    """Give user the current playlist stored in queue.

    """
    channel = ctx.author.voice.channel
    if channel in queue_dict:
        queue = queue_dict[channel]
    else:
        await ctx.send(':x: **   Playlist is empty**')
        return
    if not queue.is_empty():
        await ctx.send('**Playlist**')
        lst = queue.get_list()
        for i in range(len(lst)):
            url = lst[i]
            await ctx.send(f'**{str(i + 1)}. ** {url}')
    if queue.is_empty():
        await ctx.send(':x: **   Playlist is empty**')


@ushiko.command(aliases=['编辑歌单'])
async def edit_playlist(ctx, number: int):
    """Remove given track in the playlist

    """
    channel = ctx.author.voice.channel
    if channel in queue_dict:
        queue = queue_dict[channel]
    else:
        await ctx.send(':x: **   Playlist is empty**')
        return
    if 0 < number <= len(queue.get_list()):
        queue.remove(number - 1)
        await ctx.send(f'**Playlist item {number} has been removed**')
    else:
        await ctx.send(':x: **   Invalid item number**')


@ushiko.command(aliases=['清空歌单', '删除歌单'])
async def del_playlist(ctx):
    """Completely clear the playlist

    """
    channel = ctx.author.voice.channel
    if channel in queue_dict:
        queue = queue_dict[channel]
        queue.clear()


@ushiko.command(aliases=['下一首'])
async def skip(ctx):
    """Skip to the next song in playlist.

    """
    channel = ctx.author.voice.channel
    if channel in queue_dict:
        queue = queue_dict[channel]
    else:
        return
    for x in ushiko.voice_clients:
        voice = discord.utils.get(ushiko.voice_clients, guild=ctx.guild)
        if x.channel == ctx.author.voice.channel and voice.is_playing():
            if queue.is_looping:
                queue.is_looping = False
            x.stop()
            queue.current_song = ''
            break
        elif x.channel == ctx.author.voice.channel and not voice.is_playing():
            if queue.is_looping:
                await play(ctx, queue.current_song)
            elif not queue.is_empty():
                await play(ctx)
            break


@ushiko.command()
async def stop(ctx):
    """Stop the current playing song

    """
    channel = ctx.author.voice.channel
    # queue = queue_dict[channel]
    for x in ushiko.voice_clients:
        if x.channel == channel:
            x.stop()


@ushiko.command(aliases=['暂停'])
async def pause(ctx):
    """Pause the audio playing in user's channel

    """
    channel = ctx.author.voice.channel
    for x in ushiko.voice_clients:
        if x.channel == channel:
            x.pause()
            if channel in queue_dict:
                queue = queue_dict[channel]
                queue.is_paused = True


# Replace with your bot's token to activate
ushiko.run(os.environ['BOT_TOKEN'])
