import discord
from discord.ext import commands
import wavelink
import os
import traceback


# ============================================================
# CONFIG
# ============================================================

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

print("=" * 70)
print("STARTING BOT")
print("=" * 70)

print(f"[CONFIG] Discord token present: {bool(DISCORD_TOKEN)}")
print(f"[CONFIG] discord.py version: {discord.__version__}")
print(f"[CONFIG] wavelink version: {wavelink.__version__}")


# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()
intents.message_content = True

print("[INIT] Discord intents configured")
print(f"[INIT] Message content intent: {intents.message_content}")


# ============================================================
# BOT CLASS
# ============================================================

class Bot(commands.Bot):

    def __init__(self):

        print("[BOT] Initialising Bot instance...")

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

        print("[BOT] Bot instance created")


    # ========================================================
    # SETUP HOOK
    # ========================================================

    async def setup_hook(self):

        print("=" * 70)
        print("[SETUP] setup_hook() START")
        print("=" * 70)


        # ====================================================
        # LOAD COGS
        # ====================================================

        cog_directory = "./cogs"

        print(f"[COGS] Looking for cogs in: {cog_directory}")

        try:
            files = os.listdir(cog_directory)

        except Exception as e:

            print("[COGS] ERROR listing cog directory!")
            print(f"[COGS] Error type: {type(e).__name__}")
            print(f"[COGS] Error: {e}")

            traceback.print_exc()

            files = []

        print(f"[COGS] Files found: {files}")


        for filename in files:

            if not filename.endswith(".py"):
                print(
                    f"[COGS] Skipping non-Python file: "
                    f"{filename}"
                )
                continue

            if filename.startswith("_"):
                print(
                    f"[COGS] Skipping private file: "
                    f"{filename}"
                )
                continue

            extension = f"cogs.{filename[:-3]}"

            print("-" * 50)
            print(f"[COGS] Loading: {extension}")

            try:

                await self.load_extension(extension)

                print(
                    f"[COGS] SUCCESS: {extension}"
                )

            except Exception as e:

                print(
                    f"[COGS] FAILED: {extension}"
                )

                print(
                    f"[COGS] Error type: "
                    f"{type(e).__name__}"
                )

                print(
                    f"[COGS] Error: {e}"
                )

                traceback.print_exc()


        # ====================================================
        # SHOW LOADED COGS
        # ====================================================

        print("-" * 50)
        print("[COGS] Loaded cogs:")

        if self.cogs:

            for name, cog in self.cogs.items():

                print(
                    f"    - {name}"
                )

        else:

            print("    NONE!")


        # ====================================================
        # SHOW COMMANDS
        # ====================================================

        print("-" * 50)
        print("[COMMANDS] Registered commands:")

        if self.commands:

            for command in self.commands:

                print(
                    f"    - !{command.name} "
                    f"(Cog: {command.cog_name})"
                )

        else:

            print("    NONE!")


        # ====================================================
        # CONNECT LAVALINK
        # ====================================================

        print("-" * 50)
        print("[LAVALINK] Connecting to Lavalink...")

        try:

            nodes = [
                wavelink.Node(
                    identifier="Node1",

                    # IMPORTANT:
                    # Keep this as 127.0.0.1 because this
                    # is what your current Docker setup uses.
                    uri="http://127.0.0.1:2333",

                    password="youshallnotpass"
                )
            ]

            print(
                "[LAVALINK] Node configuration created"
            )

            print(
                "[LAVALINK] Identifier: Node1"
            )

            print(
                "[LAVALINK] URI: "
                "http://127.0.0.1:2333"
            )

            await wavelink.Pool.connect(
                nodes=nodes,
                client=self
            )

            print(
                "[LAVALINK] "
                "Pool.connect() completed"
            )

        except Exception as e:

            print(
                "[LAVALINK] FAILED TO CONNECT"
            )

            print(
                f"[LAVALINK] Error type: "
                f"{type(e).__name__}"
            )

            print(
                f"[LAVALINK] Error: {e}"
            )

            traceback.print_exc()


        print("=" * 70)
        print("[SETUP] setup_hook() COMPLETE")
        print("=" * 70)


# ============================================================
# CREATE BOT
# ============================================================

print("[BOT] Creating bot...")

bot = Bot()

print("[BOT] Bot created")


# ============================================================
# DISCORD READY
# ============================================================

@bot.event
async def on_ready():

    print()
    print("=" * 70)
    print("[DISCORD] on_ready()")
    print("=" * 70)

    print(
        f"[DISCORD] Logged in as: "
        f"{bot.user}"
    )

    print(
        f"[DISCORD] User ID: "
        f"{bot.user.id}"
    )

    print(
        f"[DISCORD] Guild count: "
        f"{len(bot.guilds)}"
    )

    print()
    print("[DISCORD] Guilds:")

    for guild in bot.guilds:

        print(
            f"    - {guild.name} "
            f"(ID: {guild.id}, "
            f"Members: {guild.member_count})"
        )


    print()
    print("[COMMANDS] Current commands:")

    for command in bot.commands:

        print(
            f"    !{command.name} "
            f"| Cog: {command.cog_name} "
            f"| Enabled: {command.enabled}"
        )


    print("=" * 70)


# ============================================================
# WAVELINK NODE READY
# ============================================================

@bot.listen("on_wavelink_node_ready")
async def on_wavelink_node_ready(
    payload: wavelink.NodeReadyEventPayload
):

    print()
    print("=" * 70)
    print("[LAVALINK] NODE READY")
    print("=" * 70)

    print(
        f"[LAVALINK] Node: "
        f"{payload.node}"
    )

    print(
        f"[LAVALINK] Session ID: "
        f"{payload.session_id}"
    )

    print(
        f"[LAVALINK] Resumed: "
        f"{payload.resumed}"
    )

    print("=" * 70)


# ============================================================
# WAVELINK WEBSOCKET CLOSED
#
# THIS IS VERY IMPORTANT FOR OUR CURRENT DEBUGGING.
# ============================================================

@bot.listen("on_wavelink_websocket_closed")
async def on_wavelink_websocket_closed(
    payload: wavelink.WebsocketClosedEventPayload
):

    print()
    print("=" * 70)
    print("!!! WAVELINK WEBSOCKET CLOSED !!!")
    print("=" * 70)

    print(
        f"[WAVELINK WS] Code: "
        f"{payload.code}"
    )

    print(
        f"[WAVELINK WS] Code value: "
        f"{getattr(payload.code, 'value', payload.code)}"
    )

    print(
        f"[WAVELINK WS] Reason: "
        f"{payload.reason}"
    )

    print(
        f"[WAVELINK WS] Closed by remote: "
        f"{payload.by_remote}"
    )

    print(
        f"[WAVELINK WS] Player: "
        f"{payload.player}"
    )


    if payload.player:

        player = payload.player

        print(
            f"[WAVELINK WS] Player connected: "
            f"{player.connected}"
        )

        print(
            f"[WAVELINK WS] Player playing: "
            f"{player.playing}"
        )

        print(
            f"[WAVELINK WS] Player paused: "
            f"{player.paused}"
        )

        print(
            f"[WAVELINK WS] Player ping: "
            f"{player.ping}"
        )

        print(
            f"[WAVELINK WS] Player position: "
            f"{player.position}"
        )

        print(
            f"[WAVELINK WS] Player current: "
            f"{player.current}"
        )

    print("=" * 70)


# ============================================================
# WAVELINK PLAYER UPDATE
#
# Lavalink periodically sends player state updates.
# This lets us see whether Lavalink is connected to Discord
# voice and what ping it reports.
# ============================================================

@bot.listen("on_wavelink_player_update")
async def on_wavelink_player_update(
    payload: wavelink.PlayerUpdateEventPayload
):

    player = payload.player

    print()
    print("[LAVALINK] PLAYER UPDATE")

    print(
        f"[LAVALINK] Connected: "
        f"{payload.connected}"
    )

    print(
        f"[LAVALINK] Ping: "
        f"{payload.ping} ms"
    )

    print(
        f"[LAVALINK] Position: "
        f"{payload.position} ms"
    )

    print(
        f"[LAVALINK] Time: "
        f"{payload.time}"
    )

    if player:

        print(
            f"[LAVALINK] Player: "
            f"{player}"
        )

        print(
            f"[LAVALINK] Player playing: "
            f"{player.playing}"
        )


# ============================================================
# WAVELINK TRACK START
# ============================================================

@bot.listen("on_wavelink_track_start")
async def on_wavelink_track_start(
    payload: wavelink.TrackStartEventPayload
):

    print()
    print("=" * 70)
    print("!!! WAVELINK TRACK START !!!")
    print("=" * 70)

    print(
        f"[TRACK] Title: "
        f"{payload.track.title}"
    )

    print(
        f"[TRACK] Identifier: "
        f"{payload.track.identifier}"
    )

    print(
        f"[TRACK] URI: "
        f"{payload.track.uri}"
    )

    print(
        f"[TRACK] Length: "
        f"{payload.track.length}"
    )

    print(
        f"[TRACK] Player: "
        f"{payload.player}"
    )

    if payload.player:

        print(
            f"[TRACK] Player connected: "
            f"{payload.player.connected}"
        )

        print(
            f"[TRACK] Player playing: "
            f"{payload.player.playing}"
        )

        print(
            f"[TRACK] Player ping: "
            f"{payload.player.ping}"
        )

    print("=" * 70)


# ============================================================
# WAVELINK TRACK END
# ============================================================

@bot.listen("on_wavelink_track_end")
async def on_wavelink_track_end(
    payload: wavelink.TrackEndEventPayload
):

    print()
    print("=" * 70)
    print("!!! WAVELINK TRACK END !!!")
    print("=" * 70)

    print(
        f"[TRACK END] Track: "
        f"{payload.track.title}"
    )

    print(
        f"[TRACK END] Reason: "
        f"{payload.reason}"
    )

    print(
        f"[TRACK END] Player: "
        f"{payload.player}"
    )

    print("=" * 70)


# ============================================================
# WAVELINK TRACK EXCEPTION
# ============================================================

@bot.listen("on_wavelink_track_exception")
async def on_wavelink_track_exception(
    payload: wavelink.TrackExceptionEventPayload
):

    print()
    print("=" * 70)
    print("!!! WAVELINK TRACK EXCEPTION !!!")
    print("=" * 70)

    print(
        f"[TRACK EXCEPTION] Track: "
        f"{payload.track.title}"
    )

    print(
        f"[TRACK EXCEPTION] Exception: "
        f"{payload.exception}"
    )

    print(
        f"[TRACK EXCEPTION] Message: "
        f"{payload.exception.message}"
    )

    print(
        f"[TRACK EXCEPTION] Severity: "
        f"{payload.exception.severity}"
    )

    print(
        f"[TRACK EXCEPTION] Player: "
        f"{payload.player}"
    )

    print("=" * 70)


# ============================================================
# WAVELINK TRACK STUCK
# ============================================================

@bot.listen("on_wavelink_track_stuck")
async def on_wavelink_track_stuck(
    payload: wavelink.TrackStuckEventPayload
):

    print()
    print("=" * 70)
    print("!!! WAVELINK TRACK STUCK !!!")
    print("=" * 70)

    print(
        f"[TRACK STUCK] Track: "
        f"{payload.track.title}"
    )

    print(
        f"[TRACK STUCK] Threshold: "
        f"{payload.threshold}"
    )

    print(
        f"[TRACK STUCK] Player: "
        f"{payload.player}"
    )

    print("=" * 70)


# ============================================================
# COMMAND ERROR
# ============================================================

@bot.event
async def on_command_error(ctx, error):

    print()
    print("=" * 70)
    print("!!! COMMAND ERROR !!!")
    print("=" * 70)

    print(
        f"[ERROR] Command: "
        f"{ctx.command}"
    )

    print(
        f"[ERROR] Author: "
        f"{ctx.author}"
    )

    print(
        f"[ERROR] Guild: "
        f"{ctx.guild}"
    )

    print(
        f"[ERROR] Channel: "
        f"{ctx.channel}"
    )

    print(
        f"[ERROR] Error type: "
        f"{type(error).__name__}"
    )

    print(
        f"[ERROR] Error: "
        f"{error}"
    )

    traceback.print_exception(
        type(error),
        error,
        error.__traceback__
    )

    print("=" * 70)


# ============================================================
# CUSTOM HELP
# ============================================================

@bot.command(name="help")
async def custom_help(ctx):

    print()
    print("=" * 70)
    print("[COMMAND] !help")
    print("=" * 70)

    print(
        f"[COMMAND] Author: "
        f"{ctx.author}"
    )

    print(
        f"[COMMAND] Guild: "
        f"{ctx.guild}"
    )

    print(
        f"[COMMAND] Channel: "
        f"{ctx.channel}"
    )


    embed = discord.Embed(
        title="Help - Music Commands",
        color=discord.Color.blue()
    )


    for cog in bot.cogs.values():

        commands_list = ""

        for command in cog.get_commands():

            if not command.hidden:

                commands_list += (
                    f"!{command.name} - "
                    f"{command.help}\n"
                )


        embed.add_field(
            name=cog.qualified_name,
            value=commands_list or "No commands",
            inline=False
        )


    await ctx.send(embed=embed)

    print("[COMMAND] !help completed")


# ============================================================
# START BOT
# ============================================================

print("=" * 70)
print("[BOT] Starting bot.run()")
print("=" * 70)


try:

    bot.run(DISCORD_TOKEN)

except Exception as e:

    print()
    print("=" * 70)
    print("[FATAL] bot.run() FAILED")
    print("=" * 70)

    print(
        f"[FATAL] Error type: "
        f"{type(e).__name__}"
    )

    print(
        f"[FATAL] Error: "
        f"{e}"
    )

    traceback.print_exc()

    raise
