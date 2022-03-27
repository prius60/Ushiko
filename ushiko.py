import discord
from discord.ext import commands
import media_fetcher
import media_queue
import asyncio
import youtube_dl
import ssl


ssl._create_default_https_context = ssl._create_unverified_context
ushiko = commands.Bot(command_prefix='')
queue = media_queue.Queue()

# Replace with your bot's token to activate
ushiko.run('')


@ushiko.event
async def on_ready():
    """Welcome info.

    """
    print('Logged in as')
    print(ushiko.user.name)
    print(ushiko.user.id)
    print('------')


@ushiko.command(aliases=['来'])
async def summon(ctx, channel=None):
    """Join user's voice channel

    """
    # await dismiss(ctx)
    for ch in ushiko.voice_clients:
        if ch.is_connected():
            await ch.move_to(ctx.author.voice.channel)
            return
    if channel is not None:
        for ch in ctx.guild.voice_channels:
            if ch.name.lower() == channel.lower():
                await ch.connect()
    else:
        destination = ctx.author.voice.channel
        await destination.connect()


@ushiko.command(aliases=['滚'])
async def dismiss(ctx, channel=None):
    """Leave a voice channel by user's request

    """
    queue.clear()
    if channel is not None:
        disconnected = False
        for ch in ushiko.voice_clients:
            if str(ch.channel).lower() == channel.lower():
                await ctx.send(':pleading_face:')
                await ch.disconnect()
                disconnected = True
            if not disconnected:
                await ctx.send(':x: **   Invalid channel name provided.**')
    else:
        for x in ushiko.voice_clients:
            if x.channel == ctx.author.voice.channel:
                await ctx.send(':pleading_face:')
                await x.disconnect()
                return
        for x in ushiko.voice_clients:
            if x.channel in ushiko.voice_clients:
                await ctx.send(':pleading_face:')
                await x.disconnect()


@ushiko.command(aliases=['整活', '播放', '继续'])
async def play(ctx, *args):
    """Play audio from provide source and keyword. Supports media from YouTube
    and BiliBili

    """

    if len(args) == 0:
        if queue.is_paused:
            for x in ushiko.voice_clients:
                if x.channel == ctx.author.voice.channel:
                    x.resume()
                    queue.is_paused = False
        elif queue.is_empty():
            await ctx.send(':x: **   Keyword or link unprovided**')
    else:
        voice = discord.utils.get(ushiko.voice_clients, guild=ctx.guild)
        keyword, source = media_fetcher.get_keyword(*args)
        url = media_fetcher.get_url(keyword, source)
        if queue.is_looping and (queue.current_song == "" or url == queue.current_song):
            queue.enqueue_with_priority(url)
        else:
            queue.enqueue(url)

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
                voice.play(media_fetcher.get_audio_YouTube(url), after=lambda e: asyncio.run_coroutine_threadsafe(skip(ctx), ushiko.loop))
                print('Ushiko is now playing media from YouTube')
            else:
                try:
                    voice.play(media_fetcher.get_audio_Bili(url), after=lambda e: asyncio.run_coroutine_threadsafe(skip(ctx), ushiko.loop))
                    print('Ushiko is now playing media from BiliBili')
                except youtube_dl.utils.DownloadError:
                    await ctx.send(':x: **   Media source unsupported**')
            if voice.is_playing():
                await ctx.send(f'**Now playing: **' + f'{url}')
                print(f'Playing {url}')
        else:
            print(f'Added to playlist: {url}')
            await ctx.send(f'**Added to playlist: **{url}')


@ushiko.command(aliases=['洗脑', '循环'])
async def loop(ctx):
    """Loop the current song

    """
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
    playlist = []
    if not queue.is_empty():
        await ctx.send('**Playlist**')
    while not queue.is_empty():
        playlist.append(queue.dequeue())
    for i in range(len(playlist)):
        url = playlist[i]
        queue.enqueue(url)
        await ctx.send(f'**{str(i+1)}. ** {url}')
    if queue.is_empty():
        await ctx.send(':x: **   Playlist is empty**')


@ushiko.command(aliases=['编辑歌单'])
async def edit_playlist(ctx, number: int):
    """Remove given track in the playlist

    """
    queue._queue.remove(number-1)


@ushiko.command(aliases=['清空歌单', '删除歌单'])
async def del_playlist(ctx):
    """Completely clear the playlist

    """
    queue.clear()


@ushiko.command(aliases=['下一首'])
async def skip(ctx):
    """Skip to the next song in playlist.

    """
    for x in ushiko.voice_clients:
        voice = discord.utils.get(ushiko.voice_clients, guild=ctx.guild)
        if x.channel == ctx.author.voice.channel and voice.is_playing():
            if queue.is_looping:
                queue.is_looping = False
            x.stop()
            queue.current_song = ''
        elif x.channel == ctx.author.voice.channel and not voice.is_playing():
            if queue.is_looping:
                await play(ctx, queue.current_song)
            elif not queue.is_empty():
                await play(ctx)
            break


@ushiko.command()
async def stop(ctx):
    """Stop the current playing song and clear the playlist

    """
    for x in ushiko.voice_clients:
        if x.channel == ctx.author.voice.channel:
            x.stop()
    queue.clear()


@ushiko.command()
async def record(ctx):
    """Record voice activity of user

    """
    raise NotImplementedError


@ushiko.command(aliases=['暂停'])
async def pause(ctx):
    """Pause the audio playing in user's channel

    """
    for x in ushiko.voice_clients:
        if x.channel == ctx.author.voice.channel:
            x.pause()
            queue.is_paused = True
