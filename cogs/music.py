import discord
from discord.ext import commands
import wavelink
import traceback

# ============================================================
# MUSIC QUEUES
# ============================================================

guild_queues = {}

# Tracks that were manually skipped.
# This prevents duplicate queue advancement if Wavelink emits
# multiple/late track-end events around a manual stop.
skipping_guilds = set()


# ============================================================
# MUSIC COG
# ============================================================

class Music(commands.Cog, name="Music Commands"):
    """Commands for controlling music playback."""

    def __init__(self, bot):
        self.bot = bot

        print("=" * 70)
        print("[MUSIC] Music cog initialised")
        print("=" * 70)

    # ========================================================
    # HELPER: GET QUEUE
    # ========================================================

    def get_queue(self, guild_id):
        return guild_queues.setdefault(guild_id, [])

    # ========================================================
    # HELPER: PLAY NEXT
    # ========================================================

    async def play_next(self, player: wavelink.Player):
        guild_id = player.guild.id
        queue = self.get_queue(guild_id)

        print("=" * 70)
        print("[QUEUE] PLAY NEXT")
        print("=" * 70)

        print(f"[QUEUE] Guild: {player.guild.name}")
        print(f"[QUEUE] Queue length: {len(queue)}")

        # ----------------------------------------------------
        # Nothing left
        # ----------------------------------------------------

        if not queue:
            print("[QUEUE] Queue is empty")
            print("[QUEUE] Disconnecting player")

            try:
                await player.disconnect()
            except Exception as e:
                print(f"[QUEUE] Disconnect error: {e}")

            print("=" * 70)
            return

        # ----------------------------------------------------
        # Get next track
        # ----------------------------------------------------

        next_track = queue.pop(0)

        print(f"[QUEUE] Next track: {next_track.title}")
        print(f"[QUEUE] Remaining tracks: {len(queue)}")

        # ----------------------------------------------------
        # Play
        # ----------------------------------------------------

        try:
            await player.play(next_track)

            print("[QUEUE] Successfully started next track")

            # Send notification
            if hasattr(player, "text_channel"):
                try:
                    await player.text_channel.send(
                        f"Now playing: **{next_track.title}**"
                    )
                except Exception as e:
                    print(f"[QUEUE] Failed to send now-playing message: {e}")

        except Exception as e:
            print("[QUEUE] FAILED TO PLAY NEXT TRACK")
            print(f"[QUEUE] Error type: {type(e).__name__}")
            print(f"[QUEUE] Error: {e}")

            traceback.print_exc()

        print("=" * 70)

    # ========================================================
    # TRACK END
    # ========================================================

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self,
        payload: wavelink.TrackEndEventPayload
    ):
        print()
        print("=" * 70)
        print("[WAVELINK] TRACK END")
        print("=" * 70)

        player = payload.player

        print(f"[WAVELINK] Player: {player}")
        print(f"[WAVELINK] Guild: {player.guild.name}")
        print(f"[WAVELINK] Track: {payload.track.title}")
        print(f"[WAVELINK] Reason: {payload.reason}")

        guild_id = player.guild.id

        # ----------------------------------------------------
        # Check whether this was a manual skip
        # ----------------------------------------------------

        if guild_id in skipping_guilds:
            print("[WAVELINK] Track ended because of manual skip")
            print("[WAVELINK] Removing skip flag")

            skipping_guilds.discard(guild_id)

        # ----------------------------------------------------
        # Always advance the queue
        # ----------------------------------------------------

        await self.play_next(player)

        print("=" * 70)

    # ========================================================
    # TRACK EXCEPTION
    # ========================================================

    @commands.Cog.listener()
    async def on_wavelink_track_exception(
        self,
        payload: wavelink.TrackExceptionEventPayload
    ):
        print()
        print("=" * 70)
        print("[WAVELINK] TRACK EXCEPTION")
        print("=" * 70)

        print(f"[WAVELINK] Track: {payload.track.title}")
        print(f"[WAVELINK] Exception: {payload.exception}")

        print("[WAVELINK] Attempting to continue queue...")

        await self.play_next(payload.player)

        print("=" * 70)

    # ========================================================
    # TRACK STUCK
    # ========================================================

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(
        self,
        payload: wavelink.TrackStuckEventPayload
    ):
        print()
        print("=" * 70)
        print("[WAVELINK] TRACK STUCK")
        print("=" * 70)

        print(f"[WAVELINK] Track: {payload.track.title}")
        print(f"[WAVELINK] Threshold: {payload.threshold}ms")

        print("[WAVELINK] Skipping stuck track...")

        await self.play_next(payload.player)

        print("=" * 70)

    # ========================================================
    # PLAY
    # ========================================================

    @commands.command(
        help="Add a song from YouTube to the queue. Usage: !play <song URL>"
    )
    async def play(self, ctx, *, search: str):

        print()
        print("=" * 70)
        print("[PLAY] !play COMMAND RECEIVED")
        print("=" * 70)

        print(f"[PLAY] Author: {ctx.author}")
        print(f"[PLAY] Guild: {ctx.guild}")
        print(f"[PLAY] Search: {search}")

        # ----------------------------------------------------
        # Voice check
        # ----------------------------------------------------

        if not ctx.author.voice:
            print("[PLAY] User is not in a voice channel")

            await ctx.send(
                "You must be in a voice channel to use this command!"
            )

            return

        author_channel = ctx.author.voice.channel

        print(f"[PLAY] Author voice channel: {author_channel}")

        # ----------------------------------------------------
        # Existing player
        # ----------------------------------------------------

        vc = ctx.voice_client

        print(f"[PLAY] Existing voice client: {vc}")

        # ----------------------------------------------------
        # Connect
        # ----------------------------------------------------

        if not vc:

            print("[PLAY] Bot is not connected")
            print("[PLAY] Connecting to voice...")

            try:
                vc = await author_channel.connect(
                    cls=wavelink.Player
                )

                print("[PLAY] Voice connection successful")

            except Exception as e:

                print("[PLAY] VOICE CONNECTION FAILED")
                print(f"[PLAY] Error type: {type(e).__name__}")
                print(f"[PLAY] Error: {e}")

                traceback.print_exc()

                await ctx.send(
                    f"Failed to connect to voice: `{type(e).__name__}`"
                )

                return

        # ----------------------------------------------------
        # Voice channel check
        # ----------------------------------------------------

        if vc.channel.id != author_channel.id:

            print("[PLAY] User and bot are in different channels")

            await ctx.send(
                "You must be in the same voice channel as the bot."
            )

            return

        # ----------------------------------------------------
        # Save text channel
        # ----------------------------------------------------

        vc.text_channel = ctx.channel

        # ----------------------------------------------------
        # Search Lavalink
        # ----------------------------------------------------

        print("[PLAY] Searching Lavalink...")
        print(f"[PLAY] Search query: {search}")

        try:
            results = await wavelink.Playable.search(search)

        except Exception as e:

            print("[PLAY] SEARCH FAILED")
            print(f"[PLAY] Error type: {type(e).__name__}")
            print(f"[PLAY] Error: {e}")

            traceback.print_exc()

            await ctx.send(
                f"Search failed: `{type(e).__name__}`"
            )

            return

        # ----------------------------------------------------
        # No results
        # ----------------------------------------------------

        if not results:

            print("[PLAY] No results found")

            await ctx.send("No song found.")

            return

        # ----------------------------------------------------
        # Select track
        # ----------------------------------------------------

        track = results[0]

        print(f"[PLAY] Selected track: {track.title}")
        print(f"[PLAY] Identifier: {track.identifier}")
        print(f"[PLAY] URI: {track.uri}")

        # ----------------------------------------------------
        # Queue
        # ----------------------------------------------------

        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)

        print(f"[QUEUE] Current queue length: {len(queue)}")
        print(f"[QUEUE] Player playing: {vc.playing}")

        # ----------------------------------------------------
        # Already playing
        # ----------------------------------------------------

        if vc.playing:

            queue.append(track)

            print("[QUEUE] Track added to queue")
            print(f"[QUEUE] New queue length: {len(queue)}")

            await ctx.send(
                f"Added to queue: `{track.title}`"
            )

        # ----------------------------------------------------
        # Nothing playing
        # ----------------------------------------------------

        else:

            print("[PLAY] Nothing currently playing")
            print("[PLAY] Starting track immediately")

            try:

                await vc.play(track)

                print("[PLAY] Track started successfully")

                await ctx.send(
                    f"Now playing: **{track.title}**"
                )

            except Exception as e:

                print("[PLAY] FAILED TO START TRACK")
                print(f"[PLAY] Error type: {type(e).__name__}")
                print(f"[PLAY] Error: {e}")

                traceback.print_exc()

                await ctx.send(
                    f"Failed to play track: `{type(e).__name__}`"
                )

        print("=" * 70)
        print("[PLAY] !play COMMAND FINISHED")
        print("=" * 70)

    # ========================================================
    # SKIP
    # ========================================================

    @commands.command(
        help="Skips the currently playing song."
    )
    async def skip(self, ctx):

        print()
        print("=" * 70)
        print("[SKIP] !skip COMMAND")
        print("=" * 70)

        vc = ctx.voice_client

        if not vc:

            print("[SKIP] No voice client")

            await ctx.send("Nothing is playing.")

            return

        if not vc.playing:

            print("[SKIP] Player is not playing")

            await ctx.send("Nothing is playing.")

            return

        guild_id = ctx.guild.id

        queue = self.get_queue(guild_id)

        print(f"[SKIP] Current track: {vc.current.title}")
        print(f"[SKIP] Queue length: {len(queue)}")

        # ----------------------------------------------------
        # Mark manual skip
        # ----------------------------------------------------

        skipping_guilds.add(guild_id)

        # ----------------------------------------------------
        # Stop current track
        # ----------------------------------------------------

        try:

            await vc.stop()

            print("[SKIP] Current track stopped")

        except Exception as e:

            print("[SKIP] STOP FAILED")
            print(f"[SKIP] Error type: {type(e).__name__}")
            print(f"[SKIP] Error: {e}")

            skipping_guilds.discard(guild_id)

            traceback.print_exc()

            await ctx.send(
                f"Failed to skip: `{type(e).__name__}`"
            )

            return

        await ctx.send("Skipped the current track.")

        print("=" * 70)

    # ========================================================
    # STOP
    # ========================================================

    @commands.command(
        help="Stops the song and clears the queue."
    )
    async def stop(self, ctx):

        print()
        print("=" * 70)
        print("[STOP] !stop COMMAND")
        print("=" * 70)

        vc = ctx.voice_client

        if not vc:

            print("[STOP] Bot is not connected")

            await ctx.send(
                "Bot is not in a voice channel."
            )

            return

        guild_id = ctx.guild.id

        # Clear queue first
        guild_queues[guild_id] = []

        # Prevent any skip handling
        skipping_guilds.discard(guild_id)

        print("[STOP] Queue cleared")

        # Stop playback
        if vc.playing:

            try:
                await vc.stop()
                print("[STOP] Playback stopped")

            except Exception as e:

                print("[STOP] Stop failed")
                print(f"[STOP] Error: {e}")

        # Disconnect
        try:

            await vc.disconnect()

            print("[STOP] Disconnected from voice")

        except Exception as e:

            print("[STOP] Disconnect failed")
            print(f"[STOP] Error: {e}")

        await ctx.send(
            "Stopped playback and cleared queue."
        )

        print("=" * 70)

    # ========================================================
    # QUEUE
    # ========================================================

    @commands.command(
        help="Shows the current queue of songs to be played."
    )
    async def queue(self, ctx):

        print()
        print("=" * 70)
        print("[QUEUE] !queue COMMAND")
        print("=" * 70)

        queue = self.get_queue(ctx.guild.id)

        print(f"[QUEUE] Guild: {ctx.guild.name}")
        print(f"[QUEUE] Queue length: {len(queue)}")

        if not queue:

            await ctx.send("Queue is empty.")

            return

        msg = "\n".join(
            f"{i + 1}. {track.title}"
            for i, track in enumerate(queue)
        )

        await ctx.send(
            f"**Queue:**\n{msg}"
        )

        print("[QUEUE] Queue displayed")
        print("=" * 70)

    # ========================================================
    # CLEAR
    # ========================================================

    @commands.command(
        help="Clears the queue."
    )
    async def clear(self, ctx):

        print()
        print("=" * 70)
        print("[CLEAR] !clear COMMAND")
        print("=" * 70)

        guild_id = ctx.guild.id

        queue = self.get_queue(guild_id)

        print(f"[CLEAR] Removing {len(queue)} tracks")

        queue.clear()

        print("[CLEAR] Queue cleared")

        await ctx.send("Queue cleared.")

        print("=" * 70)


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    print("=" * 70)
    print("[MUSIC] setup() CALLED")
    print("=" * 70)

    try:

        await bot.add_cog(Music(bot))

        print("[MUSIC] Music cog successfully added")

    except Exception as e:

        print("[MUSIC] FAILED TO ADD MUSIC COG")
        print(f"[MUSIC] Error type: {type(e).__name__}")
        print(f"[MUSIC] Error: {e}")

        traceback.print_exc()

        raise

    print("=" * 70)
    print("[MUSIC] setup() COMPLETE")
    print("=" * 70)
