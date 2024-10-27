import os

import discord
from discord.ext import commands
import media_fetcher
import media_queue
import asyncio
import yt_dlp
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
intents = discord.Intents.all()
ushiko = commands.Bot(command_prefix='', intents=intents)
queue_dict = {}
audio_dict = {}


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
    """Join the user's voice channel"""
    voice = ctx.guild.voice_client
    dest = ctx.author.voice.channel
    
    # Disconnect if bot is connected to a different channel within the same server
    if voice and voice.channel != dest:
        await dismiss(ctx)
    elif voice and voice.channel == dest:
        return
        
    await dest.connect()


@ushiko.command(aliases=['滚'])
async def dismiss(ctx):
    """Dismiss Ushiko

    """
    vc = ctx.guild.voice_client
    if vc is not None:
        if vc.channel in queue_dict:
            queue_dict.pop(vc.channel)
        await vc.disconnect(force=True)


@ushiko.command(aliases=['整活', '播放', '继续'])
async def play(ctx, *args):
    """Play audio from the provided source and keyword. Supports YouTube and BiliBili"""
    # Get or create queue for this channel
    channel = ctx.author.voice.channel
    queue = queue_dict.get(channel, media_queue.Queue())
    queue_dict[channel] = queue
    
    # Handle no arguments (resume or error)
    if not args:
        if queue.is_paused:
            ctx.guild.voice_client.resume()
            queue.is_paused = False
            return
        elif queue.is_empty():
            await ctx.send(':x: **   Provide a link or search with keywords**')
            return
    else:
        # Add new song to queue
        keyword, source = media_fetcher.get_keyword(*args)
        url = await media_fetcher.get_url(keyword, source)
        
        if queue.is_looping and (not queue.current_song or url == queue.current_song):
            queue.enqueue_with_priority(url)
        else:
            queue.enqueue(url)

    # If nothing is playing, start playback
    voice = ctx.guild.voice_client
    if not voice or not voice.is_playing() or voice.channel != channel:
        await play_next_song(ctx, queue, channel)
    else:
        print(f'Added to playlist: {url}')
        await ctx.send(f'**Added to playlist: **{url}')


async def play_next_song(ctx, queue, channel):
    """Helper function to play the next song"""
    url = queue.dequeue()
    voice = ctx.guild.voice_client
    
    # Ensure bot is in the correct channel
    if not voice or voice.channel != channel:
        await summon(ctx)
        queue_dict[channel].clear()
        print('Ushiko is now connected to users voice channel')
        voice = ctx.guild.voice_client

    # Play the audio
    try:
        audio, title = media_fetcher.get_audio_and_title(url, ctx.author.voice.channel.bitrate // 1000)
        voice.play(audio, after=lambda e: asyncio.run_coroutine_threadsafe(skip(ctx), ushiko.loop))
        
        # Clean up previous audio
        if channel in audio_dict:
            audio_dict[channel].cleanup()
        audio_dict[channel] = audio
        
        if voice.is_playing() and not queue.is_looping:
            await ctx.send(f'**Now playing: **{title}')
            print(f'Playing {title}')
    except yt_dlp.utils.DownloadError:
        await ctx.send(':x: **   Media source unsupported**')


@ushiko.command(aliases=['洗脑', '循环'])
async def loop(ctx):
    """Loop the current song

    """
    channel = ctx.author.voice.channel
    if channel in queue_dict:
        queue = queue_dict[channel]
    else:
        return
    queue.is_looping = not queue.is_looping
    await ctx.send("**Now looping**" if queue.is_looping else "**Looping is now off**")


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
    voice = ctx.guild.voice_client
    if channel in queue_dict and voice is not None:
        queue = queue_dict[channel]
    else:
        return

    if voice.is_playing():
        if queue.is_looping:
            queue.is_looping = False
        await stop(ctx)
        queue.current_song = ''
    else:
        if queue.is_looping:
            await play(ctx, queue.current_song)
        elif not queue.is_empty():
            await play(ctx)


@ushiko.command()
async def stop(ctx):
    """Stop the current playing song

    """
    ctx.guild.voice_client.stop()


@ushiko.command(aliases=['暂停'])
async def pause(ctx):
    """Pause the audio playing in user's channel

    """
    channel = ctx.author.voice.channel
    ctx.guild.voice_client.pause()
    if channel in queue_dict:
        queue_dict[channel].is_paused = True


@ushiko.event
async def on_voice_state_update(member, before, after):
    """ Clean up
    
    """
    if member == ushiko.user:
        # If the bot has disconnected from a voice channel
        if before.channel is not None and after.channel is None:
            if before.channel in audio_dict:
                audio_dict[before.channel].cleanup()
                audio_dict.pop(before.channel)

# Replace with your bot's token to activate
ushiko.run(os.environ['BOT_TOKEN'])
