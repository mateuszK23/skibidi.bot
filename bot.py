import discord
from discord.ext import commands
import yt_dlp
import random
import asyncio
import webserver
import random
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

song_queue = {}

DISCORD_TOKEN = os.environ['discordtoken']
# FFMPEG_PATH = r".\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"

proxies = [
    "203.243.63.16:80", "3.24.58.156:3128", "95.217.104.21:24815", "103.151.41.7:80", "190.113.40.202:999",
    "142.11.222.22:80", "109.111.212.78:8080", "191.97.16.160:999", "102.216.69.176:8080", "154.239.9.94:8080",
    "107.178.9.186:8080", "190.5.77.211:80", "201.229.250.21:8080", "146.59.243.214:80", "181.212.45.226:8080",
    "46.160.129.189:3128", "5.78.89.192:8080", "95.217.195.146:9999", "82.165.105.48:80", "190.111.209.207:3128",
    "144.91.106.93:3128", "34.87.103.220:80", "188.34.164.99:8080", "190.238.231.65:1994", "152.231.25.114:8080",
    "45.238.12.4:3128", "94.231.192.97:8080", "119.93.129.34:80", "181.74.81.195:999", "34.29.41.58:3128",
    "13.209.156.241:80", "212.192.31.37:3128", "45.159.150.23:3128", "103.76.253.66:3129", "137.184.197.190:80",
    "139.5.73.71:8080", "201.182.251.142:999", "46.101.102.134:3128", "200.52.148.10:999", "41.65.160.171:1981",
    "181.212.41.171:999", "41.65.55.10:1976", "181.57.131.122:8080", "201.249.152.172:999", "102.38.17.193:8080",
    "103.174.102.127:80", "174.126.217.110:80", "154.79.254.236:32650", "85.172.0.30:8080", "181.65.169.35:999",
    "163.44.253.160:80", "38.51.49.84:999", "217.219.74.130:8888", "85.221.249.213:8080", "143.42.194.37:3128",
    "14.207.24.176:8080", "190.116.2.52:80", "190.69.157.213:999", "187.141.184.235:8080", "45.229.34.174:999",
    "103.176.179.84:3128", "194.31.53.250:80", "180.180.218.250:8080", "81.44.83.70:8080", "179.1.192.17:999",
    "191.97.19.66:999", "116.203.27.109:80", "34.126.187.77:80", "66.63.168.119:8000", "45.188.166.52:1994",
    "140.83.32.175:80", "41.204.63.118:80", "1.179.148.9:55636", "43.255.113.232:84", "102.0.0.118:80",
    "45.231.221.193:999", "121.139.218.165:31409", "194.186.35.70:3128", "186.103.130.91:8080", "31.207.38.66:80",
    "207.180.250.238:80", "179.1.133.33:999", "103.155.54.26:83", "5.78.44.6:8080", "91.107.203.75:8080",
    "143.202.97.171:999", "46.105.35.193:8080", "190.61.88.147:8080", "183.88.184.48:8080", "185.174.137.30:3128",
    "143.44.191.108:8080", "92.255.205.129:8080", "193.176.242.186:80", "103.137.91.250:8080", "89.43.10.141:80",
    "81.250.223.126:80", "200.24.130.138:999", "52.41.249.10:80", "41.86.46.112:8080", "125.25.40.41:32650",
    "95.216.230.239:80", "103.51.21.250:83", "67.22.28.62:8080", "143.198.241.47:80", "213.6.155.9:19000",
    "36.229.100.73:80", "103.78.170.13:83", "196.202.210.73:32650", "43.132.184.228:8181", "190.89.37.73:999",
    "31.214.171.62:3128", "178.128.172.154:3128", "52.79.107.158:8080", "182.72.203.246:80", "103.125.154.233:8080",
    "81.161.236.152:8080", "92.118.132.125:8080", "91.213.249.200:80", "43.251.119.79:45787", "178.62.229.28:3128",
    "134.209.189.42:80", "103.243.114.206:8080", "122.52.196.36:8080", "8.242.178.5:999", "43.153.66.118:80",
    "51.159.134.210:3128", "41.86.252.91:443", "197.232.36.85:41890", "82.146.37.145:80", "157.100.6.202:999",
    "170.239.207.241:999", "3.128.142.113:80", "209.250.230.101:9090", "213.171.214.19:8001", "108.161.128.43:80",
    "202.162.105.202:8000", "181.39.27.225:1994", "61.216.156.222:60808", "77.91.74.77:80", "16.170.1.8:80",
    "154.72.90.74:8081", "24.172.34.114:49920", "103.134.165.38:8080", "59.92.70.176:3127", "165.154.236.214:80",
    "155.50.208.37:3128", "94.26.241.120:8080", "200.108.197.2:8080", "1.2.252.65:8080", "194.186.127.60:80",
    "153.19.91.77:80", "77.233.5.68:55443", "103.242.119.88:80", "203.189.150.48:8080", "20.187.77.5:80",
    "85.235.184.186:3129", "201.218.144.18:999", "181.129.43.3:8080", "64.225.4.63:9993", "190.187.201.26:8080",
    "222.255.238.159:80", "88.99.148.60:8111", "154.113.121.60:80", "41.77.188.131:80", "150.230.207.167:80",
    "155.50.241.99:3128", "46.101.19.131:80", "46.0.203.186:8080", "141.147.33.121:80", "90.154.124.211:8080",
    "64.56.150.102:3128", "54.36.81.217:8080", "46.101.160.223:80", "34.135.166.24:80", "84.241.188.138:8111",
    "190.186.237.103:80", "5.135.136.60:9090", "61.111.38.5:80", "177.93.44.53:999", "185.118.155.202:8080",
    "34.75.202.63:80", "207.180.252.117:2222", "209.145.60.213:80", "165.154.224.14:80", "146.83.118.9:80",
    "95.217.137.46:8080", "80.194.38.106:3333", "103.206.208.135:55443", "183.89.41.224:8080", "81.94.255.13:8080",
    "196.1.95.124:80", "190.71.24.129:999", "168.90.255.60:999", "159.203.104.153:8200", "45.235.123.45:999",
    "50.113.36.155:8080", "162.144.236.128:80", "103.42.28.27:45787", "58.69.201.117:8082", "78.47.103.89:8080",
    "155.50.213.149:3128", "186.159.6.163:1994", "45.61.187.67:4009", "190.136.50.67:3128", "170.210.121.190:8080",
    "103.216.51.36:32650", "149.126.101.162:8080", "18.195.164.53:7777", "41.33.66.228:1981", "46.209.54.102:8080",
    "85.238.74.91:8080", "3.143.37.255:80", "189.250.135.40:80", "184.72.36.89:80", "200.106.184.97:999",
    "103.180.73.107:8080", "159.69.214.139:3128", "24.230.33.96:3128", "125.141.151.83:80", "175.139.179.65:42580",
    "45.90.104.150:9090", "88.255.102.123:8080", "134.19.254.2:21231", "51.178.165.36:3128", "103.160.207.49:32650",
    "112.205.92.14:8080", "84.241.8.234:8080", "177.229.210.50:8080"]

def get_youtube_audio_url(url):
    """Extracts direct audio stream URL from YouTube using rotating proxies"""
    
    # Randomly select a proxy from the list
    proxy = random.choice(proxies)
    
    ydl_opts = {
        'format': 'bestaudio',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': False,
        'force_generic_extractor': False,
        'proxy': proxy, 
        'nocheckcertificate': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url'], info.get('title', 'Unknown')

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
        # source = discord.FFmpegPCMAudio(audio_url, executable=FFMPEG_PATH, **ffmpeg_options)
        source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
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

webserver.keep_alive()
bot.run(DISCORD_TOKEN)