import discord
from discord.ext import commands
import wavelink
import os

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Connect Lavalink nodes
async def connect_nodes():
    await bot.wait_until_ready()
    nodes = [
        wavelink.Node(
            identifier="Node1",
            uri="http://127.0.0.1:2333",
            password="youshallnotpass"
        )
    ]
    await wavelink.Pool.connect(nodes=nodes, client=bot)
    print("Lavalink nodes connected!")

@bot.event
async def on_ready():
    # Load all cogs
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
    
    await connect_nodes()
    print(f"Logged in as {bot.user}!")

@bot.event
async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload):
    print(f"Node with ID {payload.session_id} has connected")
    print(f"Resumed session: {payload.resumed}")


@bot.command(name="help")
async def custom_help(ctx):
    embed = discord.Embed(title="Help - Music Commands", color=discord.Color.blue())
    for cog in bot.cogs.values():
        commands_list = ""
        for command in cog.get_commands():
            if not command.hidden:
                commands_list += f"!{command.name} - {command.help}\n"
        embed.add_field(name=cog.qualified_name, value=commands_list or "No commands", inline=False)
    await ctx.send(embed=embed)

@bot.listen("on_wavelink_track_start")
async def on_track_start(payload):
    print("========== TRACK START ==========")
    print("Track:", payload.track.title)
    print("Player:", payload.player)


@bot.listen("on_wavelink_track_end")
async def on_track_end(payload):
    print("========== TRACK END ==========")
    print("Track:", payload.track.title)
    print("Reason:", payload.reason)


@bot.listen("on_wavelink_track_exception")
async def on_track_exception(payload):
    print("========== TRACK EXCEPTION ==========")
    print("Track:", payload.track.title)
    print("Exception:", payload.exception)
    print("Message:", payload.exception.message)
    print("Severity:", payload.exception.severity)


@bot.listen("on_wavelink_track_stuck")
async def on_track_stuck(payload):
    print("========== TRACK STUCK ==========")
    print("Track:", payload.track.title)
    print("Threshold:", payload.threshold)
    
bot.run(DISCORD_TOKEN)
