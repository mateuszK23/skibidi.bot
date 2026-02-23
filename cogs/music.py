import discord
from discord.ext import commands
import wavelink
import typing

guild_queues = {}  # Queue per guild

class Music(commands.Cog, name="Music Commands"):
    """Commands for controlling music playback."""

    def __init__(self, bot):
        self.bot = bot

    # Join voice helper
    async def join_channel(self, ctx):
        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel!")
            return None
        vc = ctx.voice_client
        if not vc:
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        return vc

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        guild_id = player.guild.id

        queue = guild_queues.get(guild_id, [])
        if not queue:
            await player.disconnect()
            return

        next_track = queue.pop(0)
        await player.play(next_track)

        if hasattr(player, "text_channel"):
            await player.text_channel.send(f"Now playing: **{next_track.title}**")

    @commands.command(help="Add a song from YT to the queue. Usage: !play <song URL>")
    async def play(self, ctx, search: str):

        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel to use this command!")
            return

        vc = typing.cast(wavelink.Player, ctx.voice_client)
        if not vc:
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        if ctx.author.voice.channel.id != vc.channel.id:
            return await ctx.send("You must be in the same voice channel as the bot.")

        results = await wavelink.Playable.search(search)
        if not results:
            return await ctx.send("No song found.")

        song = results[0]

        if not hasattr(vc, "text_channel"):
            vc.text_channel = ctx.channel

        if vc.playing:
            guild_queues.setdefault(ctx.guild.id, []).append(song)
            await ctx.send(f"Added to queue: `{song.title}`")
        else:
            await vc.play(song)
            await ctx.send(f"Now playing: `{song.title}`")

    @commands.command(help="Skips the currently playing song.")
    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc and vc.playing:
            await vc.stop()
            await ctx.send("Skipped the current track.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.command(help="Stops the song and clears the queue.")
    async def stop(self, ctx):
        vc = ctx.voice_client
        if vc:
            await vc.stop()
            guild_queues[ctx.guild.id] = []
            await vc.disconnect()
            await ctx.send("Stopped playback and cleared queue.")
        else:
            await ctx.send("Bot is not in a voice channel.")

    @commands.command(help="Shows the current queue of songs to be played.")
    async def queue(self, ctx):
        queue = guild_queues.get(ctx.guild.id, [])
        if not queue:
            await ctx.send("Queue is empty.")
            return
        msg = "\n".join(f"{i+1}. {track.title}" for i, track in enumerate(queue))
        await ctx.send(f"**Queue:**\n{msg}")

    @commands.command(help="Clears the queue.")
    async def clear(self, ctx):
        guild_queues[ctx.guild.id] = []
        await ctx.send("Queue cleared.")

async def setup(bot):
    await bot.add_cog(Music(bot))
