import discord
from discord.ext import commands
import yt_dlp
import random
import asyncio
import random
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

song_queue = {}

DISCORD_TOKEN = os.environ['discordtoken']
FFMPEG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'thirdparty', 'ffmpeg-7.1.1-essentials_build', 'bin', 'ffmpeg.exe' )


def get_youtube_audio_url(url):
    """Extracts direct audio stream URL from YouTube using yt-dlp without authentication."""
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio',  # Prefer audio-only formats
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        },
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get('url')
            title = info.get('title', 'Unknown')
            return audio_url, title
    except Exception as e:
        print(f"Error extracting info: {e}")
        return None, None


@bot.command()
async def play(ctx, url: str):
    """Streams a YouTube song or adds it to the queue"""
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel!")
        return

    channel = ctx.author.voice.channel
    if not ctx.voice_client:
        await channel.connect()

    audio_url, song_title = get_youtube_audio_url(url)

    if ctx.guild.id not in song_queue:
        song_queue[ctx.guild.id] = []

    song_queue[ctx.guild.id].append((song_title, audio_url))

    if not ctx.voice_client.is_playing():
        await play_next(ctx)
    else:
        await ctx.send(f"Added to queue: {song_title}")


skip_song = False  # Global flag to track skips

async def play_next(ctx):
    """Plays the next song in the queue"""
    global skip_song  # Access the flag
    if ctx.guild.id in song_queue and song_queue[ctx.guild.id]:  # Ensure there are songs left
        song_title, audio_url = song_queue[ctx.guild.id].pop(0)  # Get song info
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        # Create FFmpegPCMAudio source
        source = discord.FFmpegPCMAudio(audio_url, executable=FFMPEG_PATH, **ffmpeg_options)
        # source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
        # Attach title to the voice client source
        source.title = song_title  

        async def after_play(_):
            """Handles playing the next song after the current one ends"""
            await asyncio.sleep(1)  # Small delay prevents race conditions
            if not skip_song:  # ✅ Only play next if song ended naturally
                await play_next(ctx)
        
        skip_song = False  # Reset flag before playing
        ctx.voice_client.play(source, after=lambda _: bot.loop.call_soon_threadsafe(asyncio.create_task, after_play(None)))
        await ctx.send(f"🎵 Now playing: {song_title}")

    else:
        await ctx.send("Queue is empty. Add more songs with `!play <url>`.")


@bot.command()
async def skip(ctx):
    """Skips the current song"""
    global skip_song
    if ctx.voice_client and ctx.voice_client.is_playing():
        skip_song = True  # ✅ Set flag to prevent double play
        ctx.voice_client.stop()
        await ctx.send("Skipped!")

        # Wait a moment to avoid conflicts before playing the next song
        await asyncio.sleep(1)

        if ctx.guild.id in song_queue and song_queue[ctx.guild.id]:  # Ensure queue isn't empty
            await play_next(ctx)  # ✅ Call play_next manually only after stop
        else:
            await ctx.send("That was the last song in the queue. Add more songs with `!play <url>`.")
            await ctx.voice_client.disconnect()
    else:
        await ctx.send("No song is currently playing!")


@bot.command()
async def pause(ctx):
    """Pauses the music"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Paused ⏸️")
    else:
        await ctx.send("No music is playing currently.")


@bot.command()
async def resume(ctx):
    """Resumes the music"""
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumed ▶️")
    else:
        await ctx.send("The music is not paused.")


@bot.command()
async def kill(ctx):
    """Clears the queue and disconnects the bot"""
    if ctx.voice_client:
        song_queue[ctx.guild.id] = []  # Clear queue
        await ctx.voice_client.disconnect()
        await ctx.send("Bot disconnected and queue cleared!")
    else:
        await ctx.send("I'm not in a voice channel!")


@bot.command()
async def queue(ctx):
    """Displays the currently playing song and the queue"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        source = ctx.voice_client.source
        current_song = getattr(source, 'title', "Unknown Song")  # Get stored title
    else:
        current_song = "No song is currently playing."

    if ctx.guild.id in song_queue and song_queue[ctx.guild.id]:
        queue_list = "\n".join([f"{i+1}. {title}" for i, (title, _) in enumerate(song_queue[ctx.guild.id])])
        await ctx.send(f"🎵 **Now Playing:** {current_song}\n\n📜 **Queue:**\n{queue_list}")
    else:
        await ctx.send(f"🎵 **Now Playing:** {current_song}\n\nQueue is empty! Add songs with `!play <YouTube URL>`.")


@bot.command()
async def skibidi(ctx):
    """Play skibidi The Shoebody Bop"""
    await play(ctx, "https://www.youtube.com/watch?v=XnnLRkPRqYM")


@bot.command()
async def slow_skibidi(ctx):
    """Play slow skibidi The Shoebody Bop"""
    await play(ctx, "https://www.youtube.com/watch?v=mRNtw_Tc1Jc&ab_channel=DrueLanglois")


@bot.command()
async def showpen(ctx):
    """Pokazowka Macka"""
    await ctx.send("*Maciej pokazuje pena*")
    return


@bot.command()
async def oneshot(ctx):
    """Pokazowka Macka"""
    await ctx.send("*Maciej oneshotuje pena*")
    return


# Create a dictionary mapping roles to champions
champions_by_role = {
    "Top": [
        "Aatrox", "Akali", "Akshan", "Camille", "Cho'Gath", "Dr. Mundo", "Fiora", "Gangplank",
        "Garen", "Gnar", "Gwen", "Heimerdinger", "Illaoi", "Irelia", "Jax", "Kayle", "Kennen",
        "Kled", "KSante", "Malphite", "Maokai", "Mordekaiser", "Nasus", "Olaf", "Ornn",
        "Pantheon", "Poppy", "Quinn", "Renekton", "Riven", "Rumble", "Sett", "Shen",
        "Singed", "Sion", "Tahm Kench", "Teemo", "Tryndamere", "Urgot", "Vayne", "Vladimir",
        "Volibear", "Warwick", "Wukong", "Yorick",
    ],
    "Jungle": [
        "Amumu", "Bel'Veth", "Briar", "Diana", "Ekko", "Elise", "Evelynn", "Fiddlesticks",
        "Gragas", "Graves", "Hecarim", "Ivern", "Jarvan IV", "Karthus", "Kayn", "Kha'Zix",
        "Kindred", "Lee Sin", "Lillia", "Maokai", "Master Yi", "Nidalee", "Nocturne", "Olaf",
        "Poppy", "Rammus", "Rek'Sai", "Rengar", "Sejuani", "Shaco", "Shyvana", "Taliyah",
        "Trundle", "Udyr", "Vi", "Viego", "Volibear", "Warwick", "Wukong", "Xin Zhao",
        "Zac",
    ],
    "Mid": [
        "Ahri", "Akali", "Akshan", "Anivia", "Annie", "Aurelion Sol", "Azir", "Cassiopeia",
        "Corki", "Diana", "Ekko", "Fizz", "Heimerdinger", "Irelia", "Karma", "Karthus",
        "Kassadin", "Katarina", "LeBlanc", "Lissandra", "Lux", "Malzahar", "Neeko", "Orianna",
        "Pantheon", "Qiyana", "Ryze", "Seraphine", "Sett", "Swain", "Sylas", "Syndra",
        "Taliyah", "Twisted Fate", "Veigar", "Vel'Koz", "Vex", "Viktor", "Vladimir",
        "Xerath", "Yasuo", "Yone", "Ziggs", "Zoe",
    ],
    "ADC": [
        "Aphelios", "Ashe", "Caitlyn", "Draven", "Ezreal", "Jhin", "Jinx", "Kai'Sa",
        "Kalista", "Kog'Maw", "Lucian", "Miss Fortune", "Nilah", "Samira", "Sivir",
        "Tristana", "Twitch", "Varus", "Vayne", "Xayah", "Zeri",
    ],
    "Support": [
        "Alistar", "Bard", "Blitzcrank", "Brand", "Braum", "Janna", "Karma", "Leona",
        "Lulu", "Lux", "Milio", "Miss Fortune", "Nami", "Nautilus", "Pantheon", "Pyke",
        "Rakan", "Rell", "Renata Glasc", "Senna", "Seraphine", "Sona", "Soraka",
        "Swain", "Tahm Kench", "Taric", "Thresh", "Vel'Koz", "Xerath", "Yuumi", "Zilean",
        "Zyra",
    ],
}


def assign_roles_and_champions(name1, name2, name3, name4, name5):
    """Assigns a role and a suitable champion to each player"""
    roles = list(champions_by_role.keys())
    players = [name1, name2, name3, name4, name5]

    assigned_team = {}
    for i, player in enumerate(players):
        role = roles[i]  # Assign each player a unique role
        champion = random.choice(champions_by_role[role])  # Pick a random champion
        assigned_team[role] = {"player": player, "champion": champion}

    return assigned_team


@bot.command()
async def team(ctx, name1, name2, name3, name4, name5):
    """'!team name1, name2, name3, name4, name5' -> Assigns each player a role and a champion"""
    assigned_team = assign_roles_and_champions(name1, name2, name3, name4, name5)

    # Format the response
    response = "🎮 **Team Composition:**\n```"
    for role, data in assigned_team.items():
        response += f"{role}: {data['player']} ➝ {data['champion']}\n"
    response += "```"

    await ctx.send(response)


@bot.command()
async def ktomaracje(ctx):
    """Who's right?"""
    await ctx.send("NIE Maciek")


print(FFMPEG_PATH)
bot.run(DISCORD_TOKEN)