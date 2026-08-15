import discord
from discord.ext import commands

import aiohttp
import asyncio
import os
import traceback

from collections import Counter, defaultdict
from datetime import datetime, timezone


# ============================================================
# CONFIG
# ============================================================

RIOT_API_KEY = os.environ.get("RIOT_API_KEY")

# Riot routing:
#
# Europe routing is used for:
#   - Riot Account API
#   - Match-V5 API
#
# EUNE platform routing is used for:
#   - Ranked information
#
REGION = "europe"
PLATFORM = "eun1"

MATCHES_TO_FETCH = 100

# Current 2026 season.
#
# Change this if you want a different starting date.
SEASON_START = datetime(
    2026,
    1,
    1,
    tzinfo=timezone.utc
)

# Data Dragon version.
#
# Using "latest" makes Riot redirect to the current version.
DDRAGON_VERSION = "latest"


# ============================================================
# LOL STATS COG
# ============================================================

class LOLStats(commands.Cog, name="League of Legends"):

    """
    League of Legends statistics commands.

    !lolstats Player#TAG
    """

    def __init__(self, bot):

        self.bot = bot

        self.session = None

        print("=" * 70)
        print("[LOL] League of Legends stats cog initialised")
        print("=" * 70)

        print(
            f"[LOL] Riot API key present: "
            f"{bool(RIOT_API_KEY)}"
        )

        print(
            f"[LOL] Match region: "
            f"{REGION}"
        )

        print(
            f"[LOL] Platform: "
            f"{PLATFORM}"
        )

    # ========================================================
    # SESSION
    # ========================================================

    async def get_session(self):

        if self.session is None or self.session.closed:

            self.session = aiohttp.ClientSession(
                headers={
                    "X-Riot-Token": RIOT_API_KEY
                }
            )

        return self.session

    async def cog_unload(self):

        if self.session and not self.session.closed:

            await self.session.close()

    # ========================================================
    # RIOT API REQUEST
    # ========================================================

    async def riot_get(self, url):

        session = await self.get_session()

        print()
        print("[LOL API]")
        print(f"[LOL API] GET {url}")

        try:

            async with session.get(url) as response:

                print(
                    f"[LOL API] Status: "
                    f"{response.status}"
                )

                if response.status == 200:

                    return await response.json()

                if response.status == 401:

                    print(
                        "[LOL API] Invalid API key"
                    )

                    return None

                if response.status == 403:

                    print(
                        "[LOL API] Forbidden / expired API key"
                    )

                    return None

                if response.status == 404:

                    print(
                        "[LOL API] Resource not found"
                    )

                    return None

                if response.status == 429:

                    print(
                        "[LOL API] Rate limited"
                    )

                    return "RATE_LIMITED"

                body = await response.text()

                print(
                    f"[LOL API] Error response: "
                    f"{body[:500]}"
                )

                return None

        except Exception as e:

            print(
                "[LOL API] Request failed"
            )

            print(
                f"[LOL API] Error type: "
                f"{type(e).__name__}"
            )

            print(
                f"[LOL API] Error: {e}"
            )

            traceback.print_exc()

            return None

    # ========================================================
    # GET ACCOUNT
    # ========================================================

    async def get_account(
        self,
        game_name,
        tag_line
    ):

        url = (
            f"https://{REGION}.api.riotgames.com"
            f"/riot/account/v1/accounts/by-riot-id/"
            f"{game_name}/{tag_line}"
        )

        return await self.riot_get(url)

    # ========================================================
    # GET RANK
    # ========================================================

    async def get_rank(self, puuid):

        url = (
            f"https://{PLATFORM}.api.riotgames.com"
            f"/lol/league/v4/entries/by-puuid/"
            f"{puuid}"
        )

        return await self.riot_get(url)

    # ========================================================
    # GET MATCH IDS
    # ========================================================

    async def get_match_ids(self, puuid):

        start_time = int(
            SEASON_START.timestamp()
        )

        url = (
            f"https://{REGION}.api.riotgames.com"
            f"/lol/match/v5/matches/by-puuid/"
            f"{puuid}/ids"
            f"?startTime={start_time}"
            f"&start=0"
            f"&count={MATCHES_TO_FETCH}"
        )

        return await self.riot_get(url)

    # ========================================================
    # GET MATCH
    # ========================================================

    async def get_match(self, match_id):

        url = (
            f"https://{REGION}.api.riotgames.com"
            f"/lol/match/v5/matches/"
            f"{match_id}"
        )

        return await self.riot_get(url)

    # ========================================================
    # GET CHAMPION ICON
    # ========================================================

    def champion_icon(self, champion_name):

        return (
            "https://ddragon.leagueoflegends.com"
            f"/cdn/{DDRAGON_VERSION}/img/champion/"
            f"{champion_name}.png"
        )

    # ========================================================
    # FORMAT DURATION
    # ========================================================

    def format_duration(self, seconds):

        minutes = seconds // 60
        seconds = seconds % 60

        return f"{minutes}:{seconds:02d}"

    # ========================================================
    # FORMAT RANK
    # ========================================================

    def format_rank(self, entry):

        if not entry:

            return "Unranked"

        tier = entry.get(
            "tier",
            "UNRANKED"
        )

        division = entry.get(
            "rank",
            ""
        )

        lp = entry.get(
            "leaguePoints",
            0
        )

        tier = tier.capitalize()

        if division:

            return (
                f"{tier} {division}"
                f"\n**{lp} LP**"
            )

        return (
            f"{tier}"
            f"\n**{lp} LP**"
        )

    # ========================================================
    # BUILD STATISTICS
    # ========================================================

    def calculate_stats(
        self,
        matches,
        puuid
    ):

        wins = 0
        losses = 0

        kills = 0
        deaths = 0
        assists = 0

        champion_stats = defaultdict(
            lambda: {
                "games": 0,
                "wins": 0,
                "kills": 0,
                "deaths": 0,
                "assists": 0,
                "time": 0
            }
        )

        recent_games = []

        for match in matches:

            if not match:
                continue

            info = match.get(
                "info",
                {}
            )

            participant = None

            for p in info.get(
                "participants",
                []
            ):

                if p.get("puuid") == puuid:

                    participant = p
                    break

            if not participant:
                continue

            win = participant.get(
                "win",
                False
            )

            if win:

                wins += 1

            else:

                losses += 1

            k = participant.get(
                "kills",
                0
            )

            d = participant.get(
                "deaths",
                0
            )

            a = participant.get(
                "assists",
                0
            )

            kills += k
            deaths += d
            assists += a

            champion = participant.get(
                "championName",
                "Unknown"
            )

            duration = info.get(
                "gameDuration",
                0
            )

            champion_stats[
                champion
            ]["games"] += 1

            champion_stats[
                champion
            ]["wins"] += int(win)

            champion_stats[
                champion
            ]["kills"] += k

            champion_stats[
                champion
            ]["deaths"] += d

            champion_stats[
                champion
            ]["assists"] += a

            champion_stats[
                champion
            ]["time"] += duration

            recent_games.append({
                "champion": champion,
                "win": win,
                "kills": k,
                "deaths": d,
                "assists": a
            })

        total = wins + losses

        winrate = (
            wins / total * 100
            if total
            else 0
        )

        avg_kills = (
            kills / total
            if total
            else 0
        )

        avg_deaths = (
            deaths / total
            if total
            else 0
        )

        avg_assists = (
            assists / total
            if total
            else 0
        )

        kda = (
            (kills + assists) / deaths
            if deaths > 0
            else kills + assists
        )

        return {
            "wins": wins,
            "losses": losses,
            "games": total,
            "winrate": winrate,

            "kills": kills,
            "deaths": deaths,
            "assists": assists,

            "avg_kills": avg_kills,
            "avg_deaths": avg_deaths,
            "avg_assists": avg_assists,

            "kda": kda,

            "champions": champion_stats,

            "recent": recent_games
        }

    # ========================================================
    # CHAMPION STAT LINE
    # ========================================================

    def champion_stat_line(
        self,
        champion,
        stats
    ):

        games = stats["games"]
        wins = stats["wins"]

        kills = stats["kills"]
        deaths = stats["deaths"]
        assists = stats["assists"]

        winrate = (
            wins / games * 100
            if games
            else 0
        )

        kda = (
            (kills + assists) / deaths
            if deaths
            else kills + assists
        )

        return (
            f"**{champion}** — "
            f"{games} games · "
            f"{winrate:.0f}% WR · "
            f"{kda:.2f} KDA"
        )

    # ========================================================
    # COMMAND
    # ========================================================

    @commands.command(
        name="lolstats",
        help="Shows League of Legends stats. Usage: !lolstats Player#TAG"
    )
    async def lolstats(
        self,
        ctx,
        *,
        riot_id: str
    ):

        print()
        print("=" * 70)
        print("[LOL] !lolstats")
        print("=" * 70)

        print(
            f"[LOL] Requested by: "
            f"{ctx.author}"
        )

        print(
            f"[LOL] Riot ID: "
            f"{riot_id}"
        )

        # ====================================================
        # API KEY CHECK
        # ====================================================

        if not RIOT_API_KEY:

            await ctx.send(
                "❌ Riot API key is not configured."
            )

            print(
                "[LOL] RIOT_API_KEY missing"
            )

            return

        # ====================================================
        # PARSE RIOT ID
        # ====================================================

        if "#" not in riot_id:

            await ctx.send(
                "❌ Use the format:\n"
                "`!lolstats Player#TAG`"
            )

            return

        game_name, tag_line = riot_id.split(
            "#",
            1
        )

        game_name = game_name.strip()
        tag_line = tag_line.strip()

        if not game_name or not tag_line:

            await ctx.send(
                "❌ Invalid Riot ID.\n"
                "Example: `!lolstats Yoloduude#EUNE`"
            )

            return

        # ====================================================
        # LOADING MESSAGE
        # ====================================================

        loading_embed = discord.Embed(
            title="🔎 League of Legends Stats",
            description=(
                f"Looking up **{game_name}#{tag_line}**..."
            ),
            color=discord.Color.blue()
        )

        loading_message = await ctx.send(
            embed=loading_embed
        )

        try:

            # =================================================
            # ACCOUNT
            # =================================================

            account = await self.get_account(
                game_name,
                tag_line
            )

            if account == "RATE_LIMITED":

                await loading_message.edit(
                    embed=discord.Embed(
                        title="⏳ Riot API rate limited",
                        description=(
                            "Too many Riot API requests. "
                            "Try again in a little while."
                        ),
                        color=discord.Color.orange()
                    )
                )

                return

            if not account:

                await loading_message.edit(
                    embed=discord.Embed(
                        title="❌ Player not found",
                        description=(
                            f"I couldn't find "
                            f"**{game_name}#{tag_line}**."
                        ),
                        color=discord.Color.red()
                    )
                )

                return

            puuid = account.get(
                "puuid"
            )

            actual_game_name = account.get(
                "gameName",
                game_name
            )

            actual_tag_line = account.get(
                "tagLine",
                tag_line
            )

            print(
                f"[LOL] Found: "
                f"{actual_game_name}#{actual_tag_line}"
            )

            # =================================================
            # RANK
            # =================================================

            rank_entries = await self.get_rank(
                puuid
            )

            if rank_entries == "RATE_LIMITED":

                await loading_message.edit(
                    embed=discord.Embed(
                        title="⏳ Riot API rate limited",
                        description=(
                            "Riot API rate limit reached."
                        ),
                        color=discord.Color.orange()
                    )
                )

                return

            ranked_solo = None

            if rank_entries:

                for entry in rank_entries:

                    if (
                        entry.get("queueType")
                        == "RANKED_SOLO_5x5"
                    ):

                        ranked_solo = entry
                        break

            # =================================================
            # MATCH IDS
            # =================================================

            match_ids = await self.get_match_ids(
                puuid
            )

            if match_ids == "RATE_LIMITED":

                await loading_message.edit(
                    embed=discord.Embed(
                        title="⏳ Riot API rate limited",
                        description=(
                            "Riot API rate limit reached."
                        ),
                        color=discord.Color.orange()
                    )
                )

                return

            if not match_ids:

                await loading_message.edit(
                    embed=discord.Embed(
                        title=(
                            f"🎮 {actual_game_name}"
                        ),
                        description=(
                            "No matches were found "
                            "for the selected period."
                        ),
                        color=discord.Color.blue()
                    )
                )

                return

            print(
                f"[LOL] Matches found: "
                f"{len(match_ids)}"
            )

            # =================================================
            # FETCH MATCHES
            #
            # Do them in batches rather than firing 100
            # requests simultaneously.
            # =================================================

            matches = []

            for i in range(
                0,
                len(match_ids),
                5
            ):

                batch_ids = match_ids[
                    i:i + 5
                ]

                batch_results = await asyncio.gather(
                    *[
                        self.get_match(match_id)
                        for match_id in batch_ids
                    ]
                )

                matches.extend(
                    match
                    for match in batch_results
                    if match and match != "RATE_LIMITED"
                )

                # Small delay to be friendly to
                # Riot's rate limits.

                await asyncio.sleep(0.15)

            # =================================================
            # CALCULATE
            # =================================================

            stats = self.calculate_stats(
                matches,
                puuid
            )

            if stats["games"] == 0:

                await loading_message.edit(
                    embed=discord.Embed(
                        title=(
                            f"🎮 {actual_game_name}"
                        ),
                        description=(
                            "No usable matches were found."
                        ),
                        color=discord.Color.blue()
                    )
                )

                return

            # =================================================
            # MAIN EMBED
            # =================================================

            embed = discord.Embed(
                title=(
                    f"🎮 {actual_game_name} "
                    f"#{actual_tag_line}"
                ),
                description=(
                    "League of Legends — 2026 Season"
                ),
                color=discord.Color.from_rgb(
                    20,
                    90,
                    120
                )
            )

            # =================================================
            # RANK
            # =================================================

            if ranked_solo:

                rank_text = self.format_rank(
                    ranked_solo
                )

                embed.add_field(
                    name="🏆 Ranked Solo",
                    value=rank_text,
                    inline=True
                )

            else:

                embed.add_field(
                    name="🏆 Ranked Solo",
                    value="Unranked",
                    inline=True
                )

            # =================================================
            # OVERALL
            # =================================================

            embed.add_field(
                name="📊 Season Stats",
                value=(
                    f"**{stats['games']}** games\n"
                    f"🟢 **{stats['wins']}** wins\n"
                    f"🔴 **{stats['losses']}** losses\n"
                    f"📈 **{stats['winrate']:.1f}%** win rate"
                ),
                inline=True
            )

            # =================================================
            # KDA
            # =================================================

            embed.add_field(
                name="⚔️ KDA",
                value=(
                    f"**{stats['kda']:.2f} KDA**\n"
                    f"⚔️ {stats['avg_kills']:.1f} kills\n"
                    f"💀 {stats['avg_deaths']:.1f} deaths\n"
                    f"🤝 {stats['avg_assists']:.1f} assists"
                ),
                inline=True
            )

            # =================================================
            # MOST PLAYED CHAMPIONS
            # =================================================

            champions = sorted(
                stats["champions"].items(),
                key=lambda item: (
                    item[1]["games"],
                    item[1]["wins"]
                ),
                reverse=True
            )

            top_champions = champions[:5]

            champion_lines = []

            for champion, champion_data in top_champions:

                champion_lines.append(
                    self.champion_stat_line(
                        champion,
                        champion_data
                    )
                )

            embed.add_field(
                name="👑 Most Played Champions",
                value="\n".join(
                    champion_lines
                ),
                inline=False
            )

            # =================================================
            # RECENT FORM
            # =================================================

            recent = stats["recent"][:10]

            recent_text = ""

            for game in recent:

                symbol = (
                    "🟢"
                    if game["win"]
                    else "🔴"
                )

                recent_text += (
                    f"{symbol} "
                    f"**{game['champion']}** "
                    f"{game['kills']}/"
                    f"{game['deaths']}/"
                    f"{game['assists']}\n"
                )

            embed.add_field(
                name="🔥 Recent Games",
                value=recent_text or "No games",
                inline=False
            )

            # =================================================
            # THUMBNAIL
            # =================================================

            if top_champions:

                most_played_champion = (
                    top_champions[0][0]
                )

                embed.set_thumbnail(
                    url=self.champion_icon(
                        most_played_champion
                    )
                )

            # =================================================
            # FOOTER
            # =================================================

            embed.set_footer(
                text=(
                    "Data from Riot Games API • "
                    f"{stats['games']} matches analysed"
                )
            )

            # =================================================
            # SEND
            # =================================================

            await loading_message.edit(
                embed=embed
            )

            print(
                "[LOL] Stats successfully displayed"
            )

        except Exception as e:

            print()
            print("=" * 70)
            print("[LOL] FAILED")
            print("=" * 70)

            print(
                f"[LOL] Error type: "
                f"{type(e).__name__}"
            )

            print(
                f"[LOL] Error: {e}"
            )

            traceback.print_exc()

            error_embed = discord.Embed(
                title="❌ Failed to get League stats",
                description=(
                    "Something went wrong while "
                    "talking to the Riot API."
                ),
                color=discord.Color.red()
            )

            error_embed.add_field(
                name="Error",
                value=(
                    f"`{type(e).__name__}`"
                ),
                inline=False
            )

            await loading_message.edit(
                embed=error_embed
            )

        print("=" * 70)


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    print("=" * 70)
    print("[LOL] setup() CALLED")
    print("=" * 70)

    try:

        await bot.add_cog(
            LOLStats(bot)
        )

        print(
            "[LOL] League stats cog successfully added"
        )

    except Exception as e:

        print(
            "[LOL] FAILED TO ADD LOL STATS COG"
        )

        print(
            f"[LOL] Error type: "
            f"{type(e).__name__}"
        )

        print(
            f"[LOL] Error: {e}"
        )

        traceback.print_exc()

        raise

    print("=" * 70)
    print("[LOL] setup() COMPLETE")
    print("=" * 70)