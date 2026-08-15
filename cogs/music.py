import discord
from discord.ext import commands
import wavelink
import traceback

from urllib.parse import urlparse, parse_qs


# ============================================================
# MUSIC QUEUES
# ============================================================

guild_queues = {}

# Prevents duplicate queue advancement when a manual skip,
# track-end and exception events overlap.
skipping_guilds = set()

# Prevents a track from advancing the queue twice because
# Lavalink can emit multiple events around failures.
advancing_guilds = set()

# Stores the current "Now Playing" Discord message.
now_playing_messages = {}


# ============================================================
# MUSIC PLAYER BUTTONS
# ============================================================

class MusicPlayerView(discord.ui.View):

    def __init__(self, music_cog, guild_id):
        super().__init__(timeout=None)

        self.music_cog = music_cog
        self.guild_id = guild_id

    # ========================================================
    # NEXT BUTTON
    # ========================================================

    @discord.ui.button(
        label="Next",
        style=discord.ButtonStyle.primary,
        custom_id="music_next"
    )
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.guild_id != self.guild_id:

            await interaction.response.send_message(
                "This music player belongs to another server.",
                ephemeral=True
            )

            return

        await interaction.response.defer()

        await self.music_cog.next_track(
            interaction,
            from_button=True
        )

    # ========================================================
    # STOP BUTTON
    # ========================================================

    @discord.ui.button(
        label="Stop",
        style=discord.ButtonStyle.danger,
        custom_id="music_stop"
    )
    async def stop_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.guild_id != self.guild_id:

            await interaction.response.send_message(
                "This music player belongs to another server.",
                ephemeral=True
            )

            return

        await interaction.response.defer()

        await self.music_cog.stop_music(
            interaction,
            from_button=True
        )


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
        return guild_queues.setdefault(
            guild_id,
            []
        )

    # ========================================================
    # HELPER: CLEAN YOUTUBE URL
    # ========================================================

    def clean_youtube_url(self, url: str) -> str:

        try:

            parsed = urlparse(url)

            hostname = parsed.netloc.lower()

            if hostname.startswith("www."):
                hostname = hostname[4:]

            if hostname.endswith("youtube.com"):

                params = parse_qs(parsed.query)

                video_ids = params.get("v")

                if video_ids:

                    video_id = video_ids[0]

                    if video_id:

                        cleaned = (
                            "https://www.youtube.com/watch"
                            f"?v={video_id}"
                        )

                        print(
                            "[PLAY] YouTube video URL detected"
                        )

                        print(
                            f"[PLAY] Original URL: {url}"
                        )

                        print(
                            f"[PLAY] Cleaned URL: {cleaned}"
                        )

                        return cleaned

                return url

            if hostname == "youtu.be":

                video_id = parsed.path.strip("/")

                if video_id:

                    cleaned = (
                        "https://www.youtube.com/watch"
                        f"?v={video_id}"
                    )

                    print(
                        "[PLAY] YouTube short URL detected"
                    )

                    print(
                        f"[PLAY] Original URL: {url}"
                    )

                    print(
                        f"[PLAY] Cleaned URL: {cleaned}"
                    )

                    return cleaned

            return url

        except Exception as e:

            print(
                "[PLAY] Failed to clean YouTube URL"
            )

            print(
                f"[PLAY] Error: {e}"
            )

            traceback.print_exc()

            return url

    # ========================================================
    # HELPER: FORMAT DURATION
    # ========================================================

    def format_duration(self, milliseconds):

        if not milliseconds:
            return "Unknown"

        total_seconds = milliseconds // 1000

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:

            return (
                f"{hours}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

        return (
            f"{minutes}:"
            f"{seconds:02d}"
        )

    # ========================================================
    # HELPER: DELETE NOW PLAYING
    # ========================================================

    async def delete_now_playing_message(
        self,
        guild_id
    ):

        message = now_playing_messages.pop(
            guild_id,
            None
        )

        if not message:
            return

        try:

            await message.delete()

            print(
                f"[PLAYER] Deleted Now Playing "
                f"message for guild {guild_id}"
            )

        except discord.NotFound:

            pass

        except discord.HTTPException as e:

            print(
                "[PLAYER] Failed to delete "
                f"Now Playing message: {e}"
            )

    # ========================================================
    # HELPER: SEND NOW PLAYING
    # ========================================================

    async def send_now_playing(
        self,
        player,
        track
    ):

        if not hasattr(
            player,
            "text_channel"
        ):

            print(
                "[PLAYER] Player has no text channel"
            )

            return

        if not player.guild:

            print(
                "[PLAYER] Player has no guild"
            )

            return

        guild_id = player.guild.id

        await self.delete_now_playing_message(
            guild_id
        )

        queue = self.get_queue(
            guild_id
        )

        embed = self.create_now_playing_embed(
            track,
            len(queue)
        )

        view = MusicPlayerView(
            self,
            guild_id
        )

        try:

            message = await player.text_channel.send(
                embed=embed,
                view=view
            )

            now_playing_messages[
                guild_id
            ] = message

            print(
                "[PLAYER] Now Playing message created"
            )

        except Exception as e:

            print(
                "[PLAYER] Failed to send "
                f"Now Playing message: {e}"
            )

    # ========================================================
    # HELPER: CREATE NOW PLAYING EMBED
    # ========================================================

    def create_now_playing_embed(
        self,
        track,
        queue_length=0
    ):

        embed = discord.Embed(
            title="🎵 NOW PLAYING",
            description=(
                f"## [{track.title}]({track.uri})"
            ),
            color=discord.Color.blurple()
        )

        if getattr(
            track,
            "author",
            None
        ):

            embed.add_field(
                name="👤 Artist",
                value=track.author,
                inline=True
            )

        embed.add_field(
            name="⏱️ Duration",
            value=self.format_duration(
                track.length
            ),
            inline=True
        )

        embed.add_field(
            name="📋 Queue",
            value=f"{queue_length} song(s)",
            inline=True
        )

        artwork = getattr(
            track,
            "artwork",
            None
        )

        if artwork:

            print(
                f"[EMBED] Using artwork: {artwork}"
            )

            embed.set_image(
                url=artwork
            )

        else:

            identifier = getattr(
                track,
                "identifier",
                None
            )

            if identifier:

                thumbnail = (
                    "https://img.youtube.com/vi/"
                    f"{identifier}/maxresdefault.jpg"
                )

                embed.set_image(
                    url=thumbnail
                )

        embed.set_footer(
            text="Music Player"
        )

        return embed

    # ========================================================
    # HELPER: CREATE QUEUE EMBED
    # ========================================================

    def create_queue_embed(
        self,
        queue
    ):

        embed = discord.Embed(
            title="📋 Music Queue",
            color=discord.Color.blurple()
        )

        if not queue:

            embed.description = (
                "The queue is currently empty."
            )

            embed.set_footer(
                text="0 songs in queue"
            )

            return embed

        description = ""

        display_queue = queue[:20]

        for i, track in enumerate(
            display_queue
        ):

            duration = self.format_duration(
                track.length
            )

            description += (
                f"**{i + 1}.** "
                f"[{track.title}]({track.uri}) "
                f"`[{duration}]`\n"
            )

        if len(queue) > 20:

            description += (
                f"\n*...and "
                f"{len(queue) - 20} "
                f"more song(s)*"
            )

        embed.description = description

        embed.set_footer(
            text=f"{len(queue)} song(s) in queue"
        )

        return embed

    # ========================================================
    # HELPER: ERROR EMBED
    # ========================================================

    def create_error_embed(
        self,
        title,
        description
    ):

        return discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=discord.Color.red()
        )

    # ========================================================
    # PLAY NEXT
    # ========================================================

    async def play_next(
        self,
        player: wavelink.Player
    ):

        if player is None:

            print(
                "[QUEUE] Cannot play next: player is None"
            )

            return

        if player.guild is None:

            print(
                "[QUEUE] Cannot play next: "
                "player has no guild"
            )

            return

        guild_id = player.guild.id

        # ----------------------------------------------------
        # Prevent duplicate advancement
        # ----------------------------------------------------

        if guild_id in advancing_guilds:

            print(
                "[QUEUE] Queue advancement already "
                "in progress for this guild."
            )

            return

        advancing_guilds.add(guild_id)

        try:

            queue = self.get_queue(
                guild_id
            )

            print("=" * 70)
            print("[QUEUE] PLAY NEXT")
            print("=" * 70)

            print(
                f"[QUEUE] Guild: "
                f"{player.guild.name}"
            )

            print(
                f"[QUEUE] Queue length: "
                f"{len(queue)}"
            )

            # =================================================
            # NOTHING LEFT
            # =================================================

            if not queue:

                print(
                    "[QUEUE] Queue is empty"
                )

                await self.delete_now_playing_message(
                    guild_id
                )

                try:

                    await player.disconnect()

                except Exception as e:

                    print(
                        f"[QUEUE] Disconnect error: {e}"
                    )

                return

            # =================================================
            # GET NEXT TRACK
            # =================================================

            next_track = queue.pop(0)

            print(
                f"[QUEUE] Next track: "
                f"{next_track.title}"
            )

            print(
                f"[QUEUE] Remaining tracks: "
                f"{len(queue)}"
            )

            # =================================================
            # PLAY
            # =================================================

            try:

                await player.play(
                    next_track
                )

                print(
                    "[QUEUE] Successfully started "
                    "next track"
                )

                await self.send_now_playing(
                    player,
                    next_track
                )

            except Exception as e:

                print(
                    "[QUEUE] FAILED TO PLAY NEXT TRACK"
                )

                print(
                    f"[QUEUE] Error type: "
                    f"{type(e).__name__}"
                )

                print(
                    f"[QUEUE] Error: {e}"
                )

                traceback.print_exc()

                # Try the following track.
                if queue:

                    print(
                        "[QUEUE] Attempting following "
                        "track after playback failure..."
                    )

                    await self.play_next(
                        player
                    )

        finally:

            advancing_guilds.discard(
                guild_id
            )

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

        if player is None:

            print(
                "[WAVELINK] Player is None."
            )

            return

        if player.guild is None:

            print(
                "[WAVELINK] Player has no guild."
            )

            return

        print(
            f"[WAVELINK] Guild: "
            f"{player.guild.name}"
        )

        print(
            f"[WAVELINK] Track: "
            f"{payload.track.title}"
        )

        print(
            f"[WAVELINK] Reason: "
            f"{payload.reason}"
        )

        guild_id = player.guild.id

        if guild_id in skipping_guilds:

            print(
                "[WAVELINK] Manual skip detected"
            )

            skipping_guilds.discard(
                guild_id
            )

        await self.play_next(
            player
        )

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

        track = getattr(
            payload,
            "track",
            None
        )

        player = getattr(
            payload,
            "player",
            None
        )

        exception = getattr(
            payload,
            "exception",
            None
        )

        if track:

            print(
                f"[WAVELINK] Track: "
                f"{track.title}"
            )

        else:

            print(
                "[WAVELINK] Track: Unknown"
            )

        print(
            f"[WAVELINK] Exception: "
            f"{exception}"
        )

        if isinstance(
            exception,
            dict
        ):

            print(
                f"[WAVELINK] Message: "
                f"{exception.get('message', 'Unknown')}"
            )

            print(
                f"[WAVELINK] Severity: "
                f"{exception.get('severity', 'Unknown')}"
            )

            print(
                f"[WAVELINK] Cause: "
                f"{exception.get('cause', 'Unknown')}"
            )

            print(
                "[WAVELINK] Cause stack trace:\n"
                f"{exception.get('causeStackTrace', '')}"
            )

        else:

            print(
                f"[WAVELINK] Exception type: "
                f"{type(exception).__name__}"
            )

        if player is None:

            print(
                "[WAVELINK] Player is None."
            )

            return

        if player.guild is None:

            print(
                "[WAVELINK] Player has no guild."
            )

            return

        guild_id = player.guild.id

        # ----------------------------------------------------
        # Important:
        #
        # Don't immediately advance here if Lavalink may also
        # emit a TRACK END event for the same failure.
        #
        # We let track-end normally handle it.
        # ----------------------------------------------------

        print(
            "[WAVELINK] Track exception received."
        )

        print(
            "[WAVELINK] Waiting for track-end event "
            "before advancing queue."
        )

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

        track = getattr(
            payload,
            "track",
            None
        )

        player = getattr(
            payload,
            "player",
            None
        )

        if track:

            print(
                f"[WAVELINK] Track: "
                f"{track.title}"
            )

        print(
            f"[WAVELINK] Threshold: "
            f"{getattr(payload, 'threshold', 'Unknown')}ms"
        )

        if player is None:

            print(
                "[WAVELINK] Player is None."
            )

            return

        await self.play_next(
            player
        )

        print("=" * 70)

    # ========================================================
    # PLAY
    # ========================================================

    @commands.command(
        help=(
            "Add a song from YouTube to the queue. "
            "Usage: !play <song URL>"
        )
    )
    async def play(
        self,
        ctx,
        *,
        search: str
    ):

        print()
        print("=" * 70)
        print("[PLAY] !play COMMAND RECEIVED")
        print("=" * 70)

        print(
            f"[PLAY] Author: {ctx.author}"
        )

        print(
            f"[PLAY] Guild: {ctx.guild}"
        )

        print(
            f"[PLAY] Search: {search}"
        )

        # ====================================================
        # VOICE CHECK
        # ====================================================

        if not ctx.author.voice:

            await ctx.send(
                embed=self.create_error_embed(
                    "Voice Channel Required",
                    (
                        "You must be in a voice channel "
                        "to use this command."
                    )
                )
            )

            return

        author_channel = (
            ctx.author.voice.channel
        )

        # ====================================================
        # EXISTING PLAYER
        # ====================================================

        vc = ctx.voice_client

        # ====================================================
        # CONNECT
        # ====================================================

        if not vc:

            try:

                vc = await author_channel.connect(
                    cls=wavelink.Player
                )

                print(
                    "[PLAY] Voice connection successful"
                )

            except Exception as e:

                print(
                    "[PLAY] VOICE CONNECTION FAILED"
                )

                print(
                    f"[PLAY] Error: {e}"
                )

                traceback.print_exc()

                await ctx.send(
                    embed=self.create_error_embed(
                        "Connection Failed",
                        (
                            "I couldn't connect to the "
                            "voice channel."
                        )
                    )
                )

                return

        # ====================================================
        # VOICE CHANNEL CHECK
        # ====================================================

        if vc.channel.id != author_channel.id:

            await ctx.send(
                embed=self.create_error_embed(
                    "Different Voice Channel",
                    (
                        "You must be in the same voice "
                        "channel as the bot."
                    )
                )
            )

            return

        vc.text_channel = ctx.channel

        # ====================================================
        # CLEAN URL
        # ====================================================

        search = self.clean_youtube_url(
            search
        )

        # ====================================================
        # SEARCH
        # ====================================================

        try:

            results = await wavelink.Playable.search(
                search
            )

        except Exception as e:

            print(
                "[PLAY] SEARCH FAILED"
            )

            print(
                f"[PLAY] Error: {e}"
            )

            traceback.print_exc()

            await ctx.send(
                embed=self.create_error_embed(
                    "Search Failed",
                    (
                        "I couldn't search for that track."
                    )
                )
            )

            return

        if not results:

            await ctx.send(
                embed=self.create_error_embed(
                    "No Results",
                    (
                        "I couldn't find a song "
                        "matching that search."
                    )
                )
            )

            return

        # ====================================================
        # HANDLE RESULT
        # ====================================================

        if isinstance(
            results,
            wavelink.Playlist
        ):

            tracks = list(
                results.tracks
            )

        else:

            tracks = list(
                results
            )

        if not tracks:

            await ctx.send(
                embed=self.create_error_embed(
                    "No Results",
                    "No playable tracks were returned."
                )
            )

            return

        track = tracks[0]

        guild_id = ctx.guild.id

        queue = self.get_queue(
            guild_id
        )

        # ====================================================
        # PLAYLIST RESULT
        # ====================================================

        if isinstance(
            results,
            wavelink.Playlist
        ):

            print(
                f"[PLAY] Playlist detected: "
                f"{getattr(results, 'name', 'Unknown')}"
            )

            print(
                f"[PLAY] Playlist tracks: "
                f"{len(tracks)}"
            )

            if vc.playing:

                queue.extend(
                    tracks
                )

                await ctx.send(
                    embed=discord.Embed(
                        title="➕ Playlist Added",
                        description=(
                            f"Added **{len(tracks)}** "
                            "tracks to the queue."
                        ),
                        color=discord.Color.green()
                    )
                )

                return

            await vc.play(
                tracks[0]
            )

            queue.extend(
                tracks[1:]
            )

            await self.send_now_playing(
                vc,
                tracks[0]
            )

            return

        # ====================================================
        # SINGLE TRACK
        # ====================================================

        if vc.playing:

            queue.append(
                track
            )

            embed = discord.Embed(
                title="➕ Added to Queue",
                description=(
                    f"**[{track.title}]({track.uri})**"
                ),
                color=discord.Color.green()
            )

            embed.add_field(
                name="📋 Position",
                value=f"#{len(queue)}",
                inline=True
            )

            embed.add_field(
                name="⏱️ Duration",
                value=self.format_duration(
                    track.length
                ),
                inline=True
            )

            embed.set_footer(
                text=f"{len(queue)} song(s) in queue"
            )

            await ctx.send(
                embed=embed
            )

            return

        # ====================================================
        # START TRACK
        # ====================================================

        try:

            await vc.play(
                track
            )

            await self.send_now_playing(
                vc,
                track
            )

        except Exception as e:

            print(
                "[PLAY] FAILED TO START TRACK"
            )

            print(
                f"[PLAY] Error: {e}"
            )

            traceback.print_exc()

            await ctx.send(
                embed=self.create_error_embed(
                    "Playback Failed",
                    (
                        f"I couldn't start "
                        f"**{track.title}**."
                    )
                )
            )

        print("=" * 70)

    # ========================================================
    # PLAYLIST
    # ========================================================

    @commands.command(
        name="playlist",
        help=(
            "Adds every track from a YouTube playlist "
            "to the queue."
        )
    )
    async def playlist(
        self,
        ctx,
        *,
        url: str
    ):

        print()
        print("=" * 70)
        print("[PLAYLIST] !playlist COMMAND RECEIVED")
        print("=" * 70)

        print(
            f"[PLAYLIST] URL: {url}"
        )

        # ====================================================
        # VOICE CHECK
        # ====================================================

        if not ctx.author.voice:

            await ctx.send(
                embed=self.create_error_embed(
                    "Voice Channel Required",
                    (
                        "You must be in a voice channel "
                        "to use this command."
                    )
                )
            )

            return

        author_channel = (
            ctx.author.voice.channel
        )

        # ====================================================
        # PARSE URL
        # ====================================================

        parsed = urlparse(
            url
        )

        params = parse_qs(
            parsed.query
        )

        playlist_id = params.get(
            "list",
            [None]
        )[0]

        if not playlist_id:

            await ctx.send(
                embed=self.create_error_embed(
                    "Invalid Playlist",
                    (
                        "That URL does not contain "
                        "a YouTube `list=` parameter."
                    )
                )
            )

            return

        print(
            f"[PLAYLIST] Playlist ID: "
            f"{playlist_id}"
        )

        # ====================================================
        # MIX / RADIO CHECK
        # ====================================================

        if playlist_id.startswith(
            "RD"
        ):

            await ctx.send(
                embed=self.create_error_embed(
                    "YouTube Mix Detected",
                    (
                        "That URL is a YouTube Mix/radio "
                        "playlist rather than a normal "
                        "YouTube playlist.\n\n"
                        "Please use a normal YouTube "
                        "playlist URL."
                    )
                )
            )

            return

        # ====================================================
        # CONNECT
        # ====================================================

        vc = ctx.voice_client

        if not vc:

            try:

                vc = await author_channel.connect(
                    cls=wavelink.Player
                )

            except Exception as e:

                print(
                    "[PLAYLIST] CONNECTION FAILED"
                )

                print(
                    f"[PLAYLIST] Error: {e}"
                )

                traceback.print_exc()

                await ctx.send(
                    embed=self.create_error_embed(
                        "Connection Failed",
                        (
                            "I couldn't connect to "
                            "the voice channel."
                        )
                    )
                )

                return

        # ====================================================
        # CHANNEL CHECK
        # ====================================================

        if vc.channel.id != author_channel.id:

            await ctx.send(
                embed=self.create_error_embed(
                    "Different Voice Channel",
                    (
                        "You must be in the same voice "
                        "channel as the bot."
                    )
                )
            )

            return

        vc.text_channel = ctx.channel

        # ====================================================
        # NORMALISE PLAYLIST URL
        # ====================================================

        playlist_url = (
            "https://www.youtube.com/playlist"
            f"?list={playlist_id}"
        )

        print(
            f"[PLAYLIST] Loading: "
            f"{playlist_url}"
        )

        # ====================================================
        # LOAD PLAYLIST
        # ====================================================

        try:

            results = await wavelink.Playable.search(
                playlist_url
            )

        except Exception as e:

            print(
                "[PLAYLIST] SEARCH FAILED"
            )

            print(
                f"[PLAYLIST] Error type: "
                f"{type(e).__name__}"
            )

            print(
                f"[PLAYLIST] Error: {e}"
            )

            traceback.print_exc()

            await ctx.send(
                embed=self.create_error_embed(
                    "Playlist Load Failed",
                    (
                        "I couldn't load that playlist."
                    )
                )
            )

            return

        # ====================================================
        # DEBUG RESULT
        # ====================================================

        print(
            f"[PLAYLIST] Result type: "
            f"{type(results)}"
        )

        print(
            f"[PLAYLIST] Result length: "
            f"{len(results) if hasattr(results, '__len__') else 'N/A'}"
        )

        print(
            f"[PLAYLIST] Result repr: "
            f"{results!r}"
        )

        # ====================================================
        # EXTRACT TRACKS
        # ====================================================

        if isinstance(
            results,
            wavelink.Playlist
        ):

            print(
                "[PLAYLIST] Wavelink returned "
                "a Playlist object."
            )

            print(
                f"[PLAYLIST] Playlist name: "
                f"{getattr(results, 'name', 'Unknown')}"
            )

            tracks = list(
                results.tracks
            )

        else:

            print(
                "[PLAYLIST] Wavelink did NOT return "
                "a Playlist object."
            )

            tracks = list(
                results
            )

        # Remove None values.

        tracks = [
            track
            for track in tracks
            if track is not None
        ]

        print(
            f"[PLAYLIST] Extracted "
            f"{len(tracks)} track(s)"
        )

        # ====================================================
        # NO TRACKS
        # ====================================================

        if not tracks:

            await ctx.send(
                embed=self.create_error_embed(
                    "Playlist Empty",
                    (
                        "Lavalink returned no playable "
                        "tracks for that playlist."
                    )
                )
            )

            return

        # ====================================================
        # LOG EVERY TRACK
        # ====================================================

        print(
            "[PLAYLIST] Tracks returned:"
        )

        for index, track in enumerate(
            tracks,
            start=1
        ):

            print(
                f"[PLAYLIST] "
                f"{index}. {track.title} "
                f"({track.identifier})"
            )

        # ====================================================
        # QUEUE
        # ====================================================

        guild_id = ctx.guild.id

        queue = self.get_queue(
            guild_id
        )

        # ====================================================
        # PLAYER CURRENT STATE
        # ====================================================

        was_playing = vc.playing

        print(
            f"[PLAYLIST] Player currently playing: "
            f"{was_playing}"
        )

        print(
            f"[PLAYLIST] Current queue length: "
            f"{len(queue)}"
        )

        # ====================================================
        # START PLAYLIST
        # ====================================================

        if not was_playing:

            first_track = tracks[0]

            try:

                await vc.play(
                    first_track
                )

            except Exception as e:

                print(
                    "[PLAYLIST] FAILED TO START "
                    "FIRST TRACK"
                )

                print(
                    f"[PLAYLIST] Error type: "
                    f"{type(e).__name__}"
                )

                print(
                    f"[PLAYLIST] Error: {e}"
                )

                traceback.print_exc()

                await ctx.send(
                    embed=self.create_error_embed(
                        "Playback Failed",
                        (
                            f"I couldn't start "
                            f"**{first_track.title}**."
                        )
                    )
                )

                return

            # ------------------------------------------------
            # IMPORTANT:
            #
            # First track is playing.
            # Everything after it goes into our queue.
            # ------------------------------------------------

            remaining_tracks = tracks[1:]

            queue.extend(
                remaining_tracks
            )

            print(
                f"[PLAYLIST] Started: "
                f"{first_track.title}"
            )

            print(
                f"[PLAYLIST] Added "
                f"{len(remaining_tracks)} "
                f"remaining track(s) to queue"
            )

            await self.send_now_playing(
                vc,
                first_track
            )

        else:

            # =================================================
            # ALREADY PLAYING
            # =================================================

            queue.extend(
                tracks
            )

            print(
                f"[PLAYLIST] Added all "
                f"{len(tracks)} tracks to queue"
            )

        # ====================================================
        # SUCCESS EMBED
        # ====================================================

        embed = discord.Embed(
            title="🎶 Playlist Added",
            description=(
                f"Added **{len(tracks)}** "
                f"track(s) from the playlist."
            ),
            color=discord.Color.green()
        )

        embed.add_field(
            name="📋 Queue",
            value=f"{len(queue)} song(s)",
            inline=True
        )

        current_track = getattr(
            vc,
            "current",
            None
        )

        embed.add_field(
            name="▶️ Now Playing",
            value=(
                current_track.title
                if current_track
                else "Nothing"
            ),
            inline=True
        )

        embed.set_footer(
            text=f"Playlist: {playlist_id}"
        )

        await ctx.send(
            embed=embed
        )

        print(
            f"[PLAYLIST] Added "
            f"{len(tracks)} track(s)"
        )

        print(
            f"[QUEUE] Queue now contains "
            f"{len(queue)} track(s)"
        )

        print("=" * 70)

    # ========================================================
    # NEXT / SKIP
    # ========================================================

    @commands.command(
        name="next",
        aliases=["skip"],
        help="Skips the currently playing song."
    )
    async def next(
        self,
        ctx
    ):

        await self.next_track(
            ctx
        )

    # ========================================================
    # NEXT INTERNAL
    # ========================================================

    async def next_track(
        self,
        ctx_or_interaction,
        from_button=False
    ):

        if isinstance(
            ctx_or_interaction,
            discord.Interaction
        ):

            guild = (
                ctx_or_interaction.guild
            )

            send = (
                ctx_or_interaction.followup.send
            )

        else:

            guild = (
                ctx_or_interaction.guild
            )

            send = (
                ctx_or_interaction.send
            )

        if not guild:
            return

        vc = guild.voice_client

        if not vc:

            await send(
                embed=self.create_error_embed(
                    "Nothing Playing",
                    (
                        "The bot isn't connected "
                        "to a voice channel."
                    )
                ),
                ephemeral=from_button
            )

            return

        if not vc.playing:

            await send(
                embed=self.create_error_embed(
                    "Nothing Playing",
                    (
                        "There is nothing "
                        "currently playing."
                    )
                ),
                ephemeral=from_button
            )

            return

        current_track = vc.current

        guild_id = guild.id

        print(
            f"[NEXT] Skipping: "
            f"{current_track.title}"
        )

        skipping_guilds.add(
            guild_id
        )

        try:

            await vc.stop()

            print(
                "[NEXT] Current track stopped"
            )

        except Exception as e:

            print(
                "[NEXT] STOP FAILED"
            )

            print(
                f"[NEXT] Error: {e}"
            )

            skipping_guilds.discard(
                guild_id
            )

            traceback.print_exc()

            await send(
                embed=self.create_error_embed(
                    "Skip Failed",
                    (
                        "I couldn't skip the "
                        "current track."
                    )
                ),
                ephemeral=from_button
            )

            return

        if from_button:

            await send(
                "Skipped.",
                ephemeral=True
            )

        else:

            await send(
                embed=discord.Embed(
                    title="Skipped",
                    description=(
                        f"Skipped **{current_track.title}**."
                    ),
                    color=discord.Color.orange()
                )
            )

    # ========================================================
    # STOP
    # ========================================================

    @commands.command(
        name="stop",
        help="Stops playback and clears the queue."
    )
    async def stop(
        self,
        ctx
    ):

        await self.stop_music(
            ctx
        )

    # ========================================================
    # STOP INTERNAL
    # ========================================================

    async def stop_music(
        self,
        ctx_or_interaction,
        from_button=False
    ):

        if isinstance(
            ctx_or_interaction,
            discord.Interaction
        ):

            guild = (
                ctx_or_interaction.guild
            )

            send = (
                ctx_or_interaction.followup.send
            )

        else:

            guild = (
                ctx_or_interaction.guild
            )

            send = (
                ctx_or_interaction.send
            )

        if not guild:
            return

        vc = guild.voice_client

        if not vc:

            await send(
                embed=self.create_error_embed(
                    "Not Connected",
                    (
                        "The bot isn't in "
                        "a voice channel."
                    )
                ),
                ephemeral=from_button
            )

            return

        guild_id = guild.id

        # Clear queue.

        guild_queues[
            guild_id
        ] = []

        skipping_guilds.discard(
            guild_id
        )

        advancing_guilds.discard(
            guild_id
        )

        print(
            "[STOP] Queue cleared"
        )

        await self.delete_now_playing_message(
            guild_id
        )

        if vc.playing:

            try:

                await vc.stop()

                print(
                    "[STOP] Playback stopped"
                )

            except Exception as e:

                print(
                    f"[STOP] Stop failed: {e}"
                )

        try:

            await vc.disconnect()

            print(
                "[STOP] Disconnected from voice"
            )

        except Exception as e:

            print(
                f"[STOP] Disconnect failed: {e}"
            )

        if from_button:

            await send(
                "Stopped.",
                ephemeral=True
            )

        else:

            await send(
                embed=discord.Embed(
                    title="Playback Stopped",
                    description=(
                        "Playback stopped and the "
                        "queue was cleared."
                    ),
                    color=discord.Color.red()
                )
            )

    # ========================================================
    # QUEUE
    # ========================================================

    @commands.command(
        help="Shows the current queue."
    )
    async def queue(
        self,
        ctx
    ):

        print(
            "[QUEUE] !queue COMMAND"
        )

        queue = self.get_queue(
            ctx.guild.id
        )

        await ctx.send(
            embed=self.create_queue_embed(
                queue
            )
        )

    # ========================================================
    # CLEAR
    # ========================================================

    @commands.command(
        help="Clears the queue."
    )
    async def clear(
        self,
        ctx
    ):

        print(
            "[CLEAR] !clear COMMAND"
        )

        guild_id = ctx.guild.id

        queue = self.get_queue(
            guild_id
        )

        queue.clear()

        await ctx.send(
            embed=discord.Embed(
                title="🗑️ Queue Cleared",
                description=(
                    "All queued songs have been removed."
                ),
                color=discord.Color.orange()
            )
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    print("=" * 70)
    print("[MUSIC] setup() CALLED")
    print("=" * 70)

    try:

        await bot.add_cog(
            Music(bot)
        )

        print(
            "[MUSIC] Music cog successfully added"
        )

    except Exception as e:

        print(
            "[MUSIC] FAILED TO ADD MUSIC COG"
        )

        print(
            f"[MUSIC] Error type: "
            f"{type(e).__name__}"
        )

        print(
            f"[MUSIC] Error: {e}"
        )

        traceback.print_exc()

        raise

    print("=" * 70)
    print("[MUSIC] setup() COMPLETE")
    print("=" * 70)
