# ───────────────────────────────────────────────
#  Free Fire Premium Info Bot
#  Developer: DIGAMBER FUCKNER 👺
#  Theme: Aesthetic Navy + Cyan
#  File: cogs/infoCommands.py
#  Fully Clean + Error-Free + Premium UI
# ───────────────────────────────────────────────

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from datetime import datetime
import json
import os
import asyncio
import io
import uuid
import gc

CONFIG_FILE = "info_channels.json"


class InfoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "http://raw.thug4ff.com/info"
        self.generate_url = "http://profile.thug4ff.com/api/profile"
        self.session = aiohttp.ClientSession()
        self.config_data = self.load_config()
        self.cooldowns = {}

    # ────────────────────────────────
    # Utils
    # ────────────────────────────────

    def convert_unix_timestamp(self, timestamp: int) -> str:
        try:
            return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return "Not Available"

    def load_config(self):
        default_config = {
            "servers": {},
            "global_settings": {
                "default_all_channels": False,
                "default_cooldown": 30,
                "default_daily_limit": 30
            }
        }

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return default_config

        return default_config

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
        except:
            pass

    async def is_channel_allowed(self, ctx):
        guild_id = str(ctx.guild.id)
        allowed = self.config_data["servers"].get(guild_id, {}).get("info_channels", [])

        return True if not allowed else str(ctx.channel.id) in allowed

    # ────────────────────────────────
    # Channel Management Commands
    # ────────────────────────────────

    @commands.hybrid_command(name="setinfochannel", description="Allow a channel for info commands.")
    @commands.has_permissions(administrator=True)
    async def set_info_channel(self, ctx, channel: discord.TextChannel):

        gid = str(ctx.guild.id)
        self.config_data["servers"].setdefault(gid, {"info_channels": [], "config": {}})

        if str(channel.id) not in self.config_data["servers"][gid]["info_channels"]:
            self.config_data["servers"][gid]["info_channels"].append(str(channel.id))
            self.save_config()

        await ctx.reply(f"✅ {channel.mention} is now allowed for **info commands**")

    @commands.hybrid_command(name="removeinfochannel", description="Remove an allowed info channel.")
    @commands.has_permissions(administrator=True)
    async def remove_info_channel(self, ctx, channel: discord.TextChannel):

        gid = str(ctx.guild.id)
        if gid in self.config_data["servers"]:
            if str(channel.id) in self.config_data["servers"][gid]["info_channels"]:
                self.config_data["servers"][gid]["info_channels"].remove(str(channel.id))
                self.save_config()

        await ctx.reply(f"❌ {channel.mention} removed from allowed info channels")

    # ────────────────────────────────
    # INFO COMMAND (MAIN)
    # ────────────────────────────────

    @commands.hybrid_command(name="info", description="Get Free Fire Player Information")
    @app_commands.describe(uid="Enter Free Fire UID")
    async def player_info(self, ctx, uid: str):

        if not uid.isdigit():
            return await ctx.reply("❌ UID must be numbers only.")

        if not await self.is_channel_allowed(ctx):
            return await ctx.reply("❌ This channel is not allowed for `/info`.")

        # Cooldown
        guild_id = str(ctx.guild.id)
        default_cd = self.config_data["global_settings"]["default_cooldown"]
        cooldown = self.config_data["servers"].get(guild_id, {}).get("config", {}).get("cooldown", default_cd)

        if ctx.author.id in self.cooldowns:
            diff = (datetime.now() - self.cooldowns[ctx.author.id]).seconds
            if diff < cooldown:
                return await ctx.reply(f"⏳ Wait `{cooldown - diff}s` before next request.")

        self.cooldowns[ctx.author.id] = datetime.now()

        # API Fetch
        try:
            async with ctx.typing():
                async with self.session.get(f"{self.api_url}?uid={uid}") as r:
                    if r.status != 200:
                        return await ctx.send("⚠️ API Error. Try later.")
                    data = await r.json()
        except Exception as e:
            return await ctx.reply(f"❌ Unexpected Error: `{e}`")

        # Extract Data
        basic = data.get("basicInfo", {})
        captain = data.get("captainBasicInfo", {})
        clan = data.get("clanBasicInfo", {})
        pet = data.get("petInfo", {})
        profile = data.get("profileInfo", {})
        social = data.get("socialInfo", {})
        credit = data.get("creditScoreInfo", {})

        embed = discord.Embed(
            title="🌐 Free Fire Player Information",
            color=discord.Color.from_rgb(0, 140, 255),
            timestamp=datetime.now()
        )

        embed.set_author(name="Premium Info Engine — Digamber Fuckner 👺")
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        # Basic Info
        embed.add_field(
            name="🧩 BASIC INFO",
            value=f"""
**Name:** {basic.get('nickname', 'N/A')}
**UID:** `{uid}`
**Level:** {basic.get('level', '?')}
**Region:** {basic.get('region', '?')}
**Likes:** {basic.get('liked', '?')}
**Honor Score:** {credit.get('creditScore', '?')}
""",
            inline=False
        )

        # Activity
        embed.add_field(
            name="📊 ACCOUNT ACTIVITY",
            value=f"""
**Recent OB:** {basic.get('releaseVersion', '?')}
**BP Badges:** {basic.get('badgeCnt', '?')}
**BR Rank:** {basic.get('rankingPoints', '?')}
**CS Rank:** {basic.get('csRankingPoints', '?')}
**Created At:** {self.convert_unix_timestamp(int(basic.get('createAt', 0)))}
**Last Login:** {self.convert_unix_timestamp(int(basic.get('lastLoginAt', 0)))}
""",
            inline=False
        )

        # Overview
        embed.add_field(
            name="🎛️ ACCOUNT OVERVIEW",
            value=f"""
**Avatar ID:** {profile.get('avatarId', '?')}
**Banner ID:** {basic.get('bannerId', '?')}
**Pin ID:** {captain.get('pinId', '?')}
**Skills:** {profile.get('equipedSkills', 'None')}
""",
            inline=False
        )

        # Pet Info
        embed.add_field(
            name="🐶 PET DETAILS",
            value=f"""
**Equipped:** {pet.get('isSelected')}
**Pet Name:** {pet.get('name', 'None')}
**Pet Level:** {pet.get('level', '?')}
**Pet Exp:** {pet.get('exp', '?')}
""",
            inline=False
        )

        # Guild
        if clan:
            embed.add_field(
                name="🏛️ GUILD INFO",
                value=f"""
**Guild Name:** {clan.get('clanName')}
**Guild ID:** `{clan.get('clanId')}`
**Guild Level:** {clan.get('clanLevel')}
**Members:** {clan.get('memberNum')}/{clan.get('capacity')}
""",
                inline=False
            )

        embed.set_footer(text="Powered by Digamber Fuckner 👺 | Premium FF Engine")

        await ctx.send(embed=embed)

        # Outfit image
        try:
            async with self.session.get(f"{self.generate_url}?uid={uid}") as img_file:
                if img_file.status == 200:
                    img_data = await img_file.read()
                    file = discord.File(io.BytesIO(img_data), filename=f"outfit_{uid}.png")
                    await ctx.send(file=file)
        except:
            pass

    # Cleanup
    async def cog_unload(self):
        await self.session.close()


async def setup(bot):
    await bot.add_cog(InfoCommands(bot))
    @commands.hybrid_command(name="info", description="Displays information about a Free Fire player")
    @app_commands.describe(uid="FREE FIRE INFO")
    async def player_info(self, ctx: commands.Context, uid: str):
        guild_id = str(ctx.guild.id)

        if not uid.isdigit() or len(uid) < 6:
            return await ctx.reply(" Invalid UID! It must:\n- Be only numbers\n- Have at least 6 digits", mention_author=False)

        if not await self.is_channel_allowed(ctx):
            return await ctx.send(" This command is not allowed in this channel.", ephemeral=True)



        cooldown = self.config_data["global_settings"]["default_cooldown"]
        if guild_id in self.config_data["servers"]:
            cooldown = self.config_data["servers"][guild_id]["config"].get("cooldown", cooldown)

        if ctx.author.id in self.cooldowns:
            last_used = self.cooldowns[ctx.author.id]
            if (datetime.now() - last_used).seconds < cooldown:
                remaining = cooldown - (datetime.now() - last_used).seconds
                return await ctx.send(f" Please wait {remaining}s before using this command again", ephemeral=True)

        self.cooldowns[ctx.author.id] = datetime.now()
       

        try:
            async with ctx.typing():
                async with self.session.get(f"{self.api_url}?uid={uid}") as response:
                    if response.status == 404:
                        return await ctx.send(f" Player with UID `{uid}` not found.")
                    if response.status != 200:
                        return await ctx.send("API error. Try again later.")
                    data = await response.json()

            
            basic_info = data.get('basicInfo', {})
            captain_info = data.get('captainBasicInfo', {})
            clan_info = data.get('clanBasicInfo', {})
            credit_score_info = data.get('creditScoreInfo', {})
            pet_info = data.get('petInfo', {})
            profile_info = data.get('profileInfo', {})
            social_info = data.get('socialInfo', {})


            region = basic_info.get('region', 'Not found')

            embed = discord.Embed(
                title=" Player Information",
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            embed.add_field(name="", value="\n".join([
                "**┌  ACCOUNT BASIC INFO**",
                f"**├─ Name**: {basic_info.get('nickname', 'Not found')}",
                f"**├─ UID**: `{uid}`",
                f"**├─ Level**: {basic_info.get('level', 'Not found')} (Exp: {basic_info.get('exp', '?')})",
                f"**├─ Region**: {region}",
                f"**├─ Likes**: {basic_info.get('liked', 'Not found')}",
                f"**├─ Honor Score**: {credit_score_info.get('creditScore', 'Not found')}",
                f"**└─ Signature**: {social_info.get('signature', 'None') or 'None'}"
            ]), inline=False)
          

            embed.add_field(name="", value="\n".join([
                "**┌  ACCOUNT ACTIVITY**",
                f"**├─ Most Recent OB**: {basic_info.get('releaseVersion', '?')}",
                f"**├─ Current BP Badges**: {basic_info.get('badgeCnt', 'Not found')}",
                f"**├─ BR Rank**: {'' if basic_info.get('showBrRank') else 'Not found'} {basic_info.get('rankingPoints', '?')}",
                f"**├─ CS Rank**: {'' if basic_info.get('showCsRank') else 'Not found'} {basic_info.get('csRankingPoints', '?')} ",
                f"**├─ Created At**: {self.convert_unix_timestamp(int(basic_info.get('createAt', 'Not found')))}",
                f"**└─ Last Login**: {self.convert_unix_timestamp(int(basic_info.get('lastLoginAt', 'Not found')))}"

            ]), inline=False)

            embed.add_field(name="", value="\n".join([
                "**┌  ACCOUNT OVERVIEW**",
                f"**├─ Avatar ID**: {profile_info.get('avatarId', 'Not found')}",
                f"**├─ Banner ID**: {basic_info.get('bannerId', 'Not found')}",
                f"**├─ Pin ID**: {captain_info.get('pinId', 'Not found') if captain_info else 'Default'}",
                f"**└─ Equipped Skills**: {profile_info.get('equipedSkills', 'Not found')}"
            ]), inline=False)

            embed.add_field(name="", value="\n".join([
                "**┌  PET DETAILS**",
                f"**├─ Equipped?**: {'Yes' if pet_info.get('isSelected') else 'Not Found'}",
                f"**├─ Pet Name**: {pet_info.get('name', 'Not Found')}",
                f"**├─ Pet Exp**: {pet_info.get('exp', 'Not Found')}",
                f"**└─ Pet Level**: {pet_info.get('level', 'Not Found')}"
            ]), inline=False)

            if clan_info:
                guild_info = [
                    "**┌  GUILD INFO**",
                    f"**├─ Guild Name**: {clan_info.get('clanName', 'Not found')}",
                    f"**├─ Guild ID**: `{clan_info.get('clanId', 'Not found')}`",
                    f"**├─ Guild Level**: {clan_info.get('clanLevel', 'Not found')}",
                    f"**├─ Live Members**: {clan_info.get('memberNum', 'Not found')}/{clan_info.get('capacity', '?')}"
                ]
                if captain_info:
                    guild_info.extend([
                        "**└─ Leader Info**:",
                        f"    **├─ Leader Name**: {captain_info.get('nickname', 'Not found')}",
                        f"    **├─ Leader UID**: `{captain_info.get('accountId', 'Not found')}`",
                        f"    **├─ Leader Level**: {captain_info.get('level', 'Not found')} (Exp: {captain_info.get('exp', '?')})",
                        f"    **├─ Last Login**: {self.convert_unix_timestamp(int(captain_info.get('lastLoginAt', 'Not found')))}",
                        f"    **├─ Title**: {captain_info.get('title', 'Not found')}",
                        f"    **├─ BP Badges**: {captain_info.get('badgeCnt', '?')}",
                        f"    **├─ BR Rank**: {'' if captain_info.get('showBrRank') else 'Not found'} {captain_info.get('rankingPoints', 'Not found')}",
                        f"    **└─ CS Rank**: {'' if captain_info.get('showCsRank') else 'Not found'} {captain_info.get('csRankingPoints', 'Not found')} "
                    ])
                embed.add_field(name="", value="\n".join(guild_info), inline=False)



            embed.set_footer(text="DEVELOPED BY THUG")
            await ctx.send(embed=embed)

            if region and uid:
                try:
                    image_url = f"{self.generate_url}?uid={uid}"
                    print(f"Url d'image = {image_url}")
                    if image_url:
                        async with self.session.get(image_url) as img_file:
                            if img_file.status == 200:
                                with io.BytesIO(await img_file.read()) as buf:
                                    file = discord.File(buf, filename=f"outfit_{uuid.uuid4().hex[:8]}.png")
                                    await ctx.send(file=file)  # ✅ ENVOYER L'IMAGE
                                    print("Image envoyée avec succès")
                            else:
                                print(f"Erreur HTTP: {img_file.status}")
                except Exception as e:
                    print("Image generation failed:", e)

        except Exception as e:
            await ctx.send(f" Unexpected error: `{e}`")
        finally:
            gc.collect()


    async def cog_unload(self):
        await self.session.close()

    async def _send_player_not_found(self, ctx, uid):
        embed = discord.Embed(
            title="❌ Player Not Found",
            description=(
                f"UID `{uid}` not found or inaccessible.\n\n"
                "⚠️ **Note:** IND servers are currently not working."
            ),
            color=0xE74C3C
        )
        embed.add_field(
            name="Tip",
            value="- Make sure the UID is correct\n- Try a different UID",
            inline=False
        )
        await ctx.send(embed=embed, ephemeral=True)

    async def _send_api_error(self, ctx):
        await ctx.send(embed=discord.Embed(
            title="⚠️ API Error",
            description="The Free Fire API is not responding. Try again later.",
            color=0xF39C12
        ))



async def setup(bot):
    await bot.add_cog(InfoCommands(bot))
# cogs/infoCommands.py
"""
Rebranded InfoCommands Cog
Author: Digamber Fuckner
Theme: Aesthetic Navy + Cyan
"""

import os
import json
import io
import uuid
import gc
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Tuple

import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

CONFIG_FILE = "info_channels.json"

# Theme colors (navy + cyan accents)
EMBED_COLOR = 0x0F9AA6  # cyan-ish accent
NAVY_COLOR = 0x0F172A

def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def utc_from_unix(ts: int) -> Optional[datetime]:
    try:
        # ensure ts is int
        ts_i = safe_int(ts, None)
        if ts_i is None:
            return None
        return datetime.fromtimestamp(ts_i, tz=timezone.utc)
    except Exception:
        return None

def format_unix(ts: int) -> str:
    dt = utc_from_unix(ts)
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    return "Not found"

def is_interaction_ctx(ctx) -> bool:
    # Determine if we are in an interaction context that supports ephemeral
    return hasattr(ctx, "interaction") and ctx.interaction is not None

def make_embed(
    title: str,
    description: Optional[str] = None,
    fields: Optional[List[Tuple[str, str, bool]]] = None,
    thumbnail: Optional[str] = None,
    author_name: str = "Digamber Fuckner",
    footer_text: Optional[str] = None,
    color: int = EMBED_COLOR
) -> discord.Embed:
    e = discord.Embed(title=title, description=description or discord.Embed.Empty, color=color, timestamp=datetime.now(tz=timezone.utc))
    if fields:
        for name, value, inline in fields:
            # keep field names and values safe
            e.add_field(name=name or "\u200b", value=value or "—", inline=inline)
    if thumbnail:
        try:
            e.set_thumbnail(url=thumbnail)
        except Exception:
            pass
    e.set_author(name=author_name)
    e.set_footer(text=footer_text or f"Rebranded by Digamber Fuckner • Aesthetic Navy + Cyan")
    return e


class InfoCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Keep existing API endpoints
        self.api_url = "http://raw.thug4ff.com/info"
        self.generate_url = "http://profile.thug4ff.com/api/profile"
        self.session: Optional[aiohttp.ClientSession] = None
        # config holds server-specific allowed channels and settings
        self.config_data = self.load_config()
        # cooldowns per user (datetime)
        self.cooldowns = {}
        # ensure session created lazily
        self._session_lock = asyncio.Lock()

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            async with self._session_lock:
                if self.session is None or self.session.closed:
                    self.session = aiohttp.ClientSession()

    def convert_unix_timestamp(self, timestamp) -> str:
        # Accept strings or ints; return formatted UTC time or "Not found"
        try:
            return format_unix(timestamp)
        except Exception:
            return "Not found"

    def load_config(self):
        default_config = {
            "servers": {},
            "global_settings": {
                "default_all_channels": False,
                "default_cooldown": 30,
                "default_daily_limit": 30
            }
        }

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    loaded_config.setdefault("global_settings", {})
                    loaded_config["global_settings"].setdefault("default_all_channels", False)
                    loaded_config["global_settings"].setdefault("default_cooldown", 30)
                    loaded_config["global_settings"].setdefault("default_daily_limit", 30)
                    loaded_config.setdefault("servers", {})
                    return loaded_config
            except (json.JSONDecodeError, IOError) as e:
                print(f"[infoCommands] Error loading config: {e}")
                return default_config
        return default_config

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"[infoCommands] Error saving config: {e}")

    async def is_channel_allowed(self, ctx) -> bool:
        try:
            if not ctx.guild:
                # allow in DMs for debug
                return True
            guild_id = str(ctx.guild.id)
            allowed_channels = self.config_data["servers"].get(guild_id, {}).get("info_channels", [])
            # If no channels configured, allow all channels
            if not allowed_channels:
                return True
            return str(ctx.channel.id) in allowed_channels
        except Exception as e:
            print(f"[infoCommands] Error checking channel permission: {e}")
            return False

    @commands.hybrid_command(name="setinfochannel", description="Allow a channel for !info commands")
    @commands.has_permissions(administrator=True)
    async def set_info_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        self.config_data["servers"].setdefault(guild_id, {"info_channels": [], "config": {}})
        if str(channel.id) not in self.config_data["servers"][guild_id]["info_channels"]:
            self.config_data["servers"][guild_id]["info_channels"].append(str(channel.id))
            self.save_config()
            await ctx.send(f"✅ {channel.mention} is now allowed for `!info` commands")
        else:
            await ctx.send(f"ℹ️ {channel.mention} is already allowed for `!info` commands")

    @commands.hybrid_command(name="removeinfochannel", description="Remove a channel from !info commands")
    @commands.has_permissions(administrator=True)
    async def remove_info_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        if guild_id in self.config_data["servers"]:
            if str(channel.id) in self.config_data["servers"][guild_id]["info_channels"]:
                self.config_data["servers"][guild_id]["info_channels"].remove(str(channel.id))
                self.save_config()
                await ctx.send(f"✅ {channel.mention} has been removed from allowed channels")
            else:
                await ctx.send(f"❌ {channel.mention} is not in the list of allowed channels")
        else:
            await ctx.send("ℹ️ This server has no saved configuration")

    @commands.hybrid_command(name="infochannels", description="List allowed channels")
    async def list_info_channels(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id) if ctx.guild else None

        if guild_id and guild_id in self.config_data["servers"] and self.config_data["servers"][guild_id]["info_channels"]:
            channels_display = []
            for channel_id in self.config_data["servers"][guild_id]["info_channels"]:
                ch = ctx.guild.get_channel(int(channel_id)) if ctx.guild else None
                channels_display.append(f"• {ch.mention if ch else f'ID: {channel_id}'}")
            cooldown = self.config_data["servers"][guild_id]["config"].get("cooldown", self.config_data["global_settings"]["default_cooldown"])
            embed = make_embed(
                title="Allowed channels for !info",
                description="\n".join(channels_display),
                fields=None,
                author_name="Digamber Fuckner",
                footer_text=f"Current cooldown: {cooldown} seconds",
                color=NAVY_COLOR
            )
        else:
            embed = make_embed(
                title="Allowed channels for !info",
                description="All channels are allowed (no restriction configured)",
                author_name="Digamber Fuckner",
                color=NAVY_COLOR
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="info", description="Displays information about a Free Fire player")
    @app_commands.describe(uid="FREE FIRE UID (numbers only)")
    async def player_info(self, ctx: commands.Context, uid: str):
        # Basic validation
        if not uid or not uid.isdigit() or len(uid) < 6:
            # use reply for better context
            return await ctx.reply("❌ Invalid UID! It must:\n- Contain only numbers\n- Have at least 6 digits", mention_author=False)

        if not await self.is_channel_allowed(ctx):
            # if invoked as interaction, attempt ephemeral reply via interaction response
            if is_interaction_ctx(ctx):
                try:
                    await ctx.respond("❌ This command is not allowed in this channel.", ephemeral=True)
                except Exception:
                    await ctx.send("❌ This command is not allowed in this channel.")
            else:
                await ctx.send("❌ This command is not allowed in this channel.")
            return

        # Determine cooldown for server (fallback to global)
        guild_id = str(ctx.guild.id) if ctx.guild else None
        cooldown = self.config_data["global_settings"].get("default_cooldown", 30)
        if guild_id and guild_id in self.config_data["servers"]:
            cooldown = self.config_data["servers"][guild_id]["config"].get("cooldown", cooldown)

        # Check per-user cooldown
        user_id = getattr(ctx.author, "id", None)
        if user_id in self.cooldowns:
            last_used = self.cooldowns[user_id]
            diff = (datetime.now(tz=timezone.utc) - last_used).total_seconds()
            if diff < cooldown:
                remaining = int(cooldown - diff)
                # ephemeral where possible
                if is_interaction_ctx(ctx):
                    try:
                        await ctx.respond(f"⏳ Please wait {remaining}s before using this command again", ephemeral=True)
                    except Exception:
                        await ctx.send(f"⏳ Please wait {remaining}s before using this command again")
                else:
                    await ctx.send(f"⏳ Please wait {remaining}s before using this command again")
                return

        # set cooldown timestamp
        self.cooldowns[user_id] = datetime.now(tz=timezone.utc)

        # perform API request
        try:
            await self._ensure_session()
            async with ctx.typing():
                url = f"{self.api_url}?uid={uid}"
                async with self.session.get(url, timeout=20) as response:
                    if response.status == 404:
                        return await ctx.send(f"❌ Player with UID `{uid}` not found.")
                    if response.status != 200:
                        return await ctx.send("⚠️ API error. Try again later.")
                    try:
                        data = await response.json()
                    except Exception:
                        return await ctx.send("⚠️ API returned invalid data. Try again later.")

            # Extract sections safely
            basic_info = data.get("basicInfo", {}) or {}
            captain_info = data.get("captainBasicInfo", {}) or {}
            clan_info = data.get("clanBasicInfo", {}) or {}
            credit_score_info = data.get("creditScoreInfo", {}) or {}
            pet_info = data.get("petInfo", {}) or {}
            profile_info = data.get("profileInfo", {}) or {}
            social_info = data.get("socialInfo", {}) or {}

            region = basic_info.get("region", "Not found")

            # Build neat, readable fields (keeps one field but many lines for visual compactness)
            basic_lines = [
                "**┌  ACCOUNT BASIC INFO**",
                f"**├─ Name**: {basic_info.get('nickname', 'Not found')}",
                f"**├─ UID**: `{uid}`",
                f"**├─ Level**: {basic_info.get('level', 'Not found')} (Exp: {basic_info.get('exp', '?')})",
                f"**├─ Region**: {region}",
                f"**├─ Likes**: {basic_info.get('liked', 'Not found')}",
                f"**├─ Honor Score**: {credit_score_info.get('creditScore', 'Not found')}",
                f"**└─ Signature**: {social_info.get('signature') or 'None'}"
            ]

            activity_lines = [
                "**┌  ACCOUNT ACTIVITY**",
                f"**├─ Most Recent OB**: {basic_info.get('releaseVersion', '?')}",
                f"**├─ Current BP Badges**: {basic_info.get('badgeCnt', 'Not found')}",
                f"**├─ BR Rank**: {basic_info.get('rankingPoints', 'Not found')}",
                f"**├─ CS Rank**: {basic_info.get('csRankingPoints', 'Not found')}",
                f"**├─ Created At**: {self.convert_unix_timestamp(basic_info.get('createAt'))}",
                f"**└─ Last Login**: {self.convert_unix_timestamp(basic_info.get('lastLoginAt'))}"
            ]

            overview_lines = [
                "**┌  ACCOUNT OVERVIEW**",
                f"**├─ Avatar ID**: {profile_info.get('avatarId', 'Not found')}",
                f"**├─ Banner ID**: {basic_info.get('bannerId', 'Not found')}",
                f"**├─ Pin ID**: {captain_info.get('pinId', 'Not found') if captain_info else 'Default'}",
                f"**└─ Equipped Skills**: {profile_info.get('equipedSkills', 'Not found')}"
            ]

            pet_lines = [
                "**┌  PET DETAILS**",
                f"**├─ Equipped?**: {'Yes' if pet_info.get('isSelected') else 'Not Found'}",
                f"**├─ Pet Name**: {pet_info.get('name', 'Not Found')}",
                f"**├─ Pet Exp**: {pet_info.get('exp', 'Not Found')}",
                f"**└─ Pet Level**: {pet_info.get('level', 'Not Found')}"
            ]

            # Compose embed
            thumbnail_url = ctx.author.display_avatar.url if getattr(ctx.author, "display_avatar", None) else None
            embed = make_embed(
                title="Player Information",
                description="Premium rebrand — clean developer look.",
                fields=[
                    ("\u200b", "\n".join(basic_lines), False),
                    ("\u200b", "\n".join(activity_lines), False),
                    ("\u200b", "\n".join(overview_lines), False),
                    ("\u200b", "\n".join(pet_lines), False),
                ],
                thumbnail=thumbnail_url,
                author_name="Digamber Fuckner",
                color=EMBED_COLOR
            )

            # If clan/guild exists, add as separate field
            if clan_info:
                guild_info = [
                    "**┌  GUILD INFO**",
                    f"**├─ Guild Name**: {clan_info.get('clanName', 'Not found')}",
                    f"**├─ Guild ID**: `{clan_info.get('clanId', 'Not found')}`",
                    f"**├─ Guild Level**: {clan_info.get('clanLevel', 'Not found')}",
                    f"**├─ Live Members**: {clan_info.get('memberNum', 'Not found')}/{clan_info.get('capacity', '?')}"
                ]
                if captain_info:
                    guild_info.extend([
                        "**└─ Leader Info**:",
                        f"    **├─ Leader Name**: {captain_info.get('nickname', 'Not found')}",
                        f"    **├─ Leader UID**: `{captain_info.get('accountId', 'Not found')}`",
                        f"    **├─ Leader Level**: {captain_info.get('level', 'Not found')} (Exp: {captain_info.get('exp', '?')})",
                        f"    **├─ Last Login**: {self.convert_unix_timestamp(captain_info.get('lastLoginAt'))}",
                        f"    **├─ Title**: {captain_info.get('title', 'Not found')}",
                        f"    **├─ BP Badges**: {captain_info.get('badgeCnt', '?')}",
                        f"    **├─ BR Rank**: {captain_info.get('rankingPoints', 'Not found')}",
                        f"    **└─ CS Rank**: {captain_info.get('csRankingPoints', 'Not found')}"
                    ])
                embed.add_field(name="\u200b", value="\n".join(guild_info), inline=False)

            await ctx.send(embed=embed)

            # Try generating and sending profile image if available
            if region and uid:
                try:
                    await self._ensure_session()
                    image_url = f"{self.generate_url}?uid={uid}"
                    async with self.session.get(image_url, timeout=30) as img_resp:
                        if img_resp.status == 200:
                            img_data = await img_resp.read()
                            if img_data:
                                buf = io.BytesIO(img_data)
                                buf.seek(0)
                                filename = f"outfit_{uuid.uuid4().hex[:8]}.png"
                                file = discord.File(buf, filename=filename)
                                await ctx.send(file=file)
                        else:
                            # log non-200 image responses for debugging
                            print(f"[infoCommands] Image HTTP {img_resp.status} for uid={uid}")
                except Exception as e:
                    print(f"[infoCommands] Image generation failed: {e}")

        except Exception as e:
            # send error embed (safe)
            err_embed = make_embed(
                title="Unexpected error",
                description=f"`{e}`",
                author_name="Digamber Fuckner",
                color=0xE74C3C
            )
            try:
                await ctx.send(embed=err_embed)
            except Exception:
                # fallback to plain text
                await ctx.send(f"Unexpected error: `{e}`")
        finally:
            # attempt GC but avoid heavy operations
            try:
                gc.collect()
            except Exception:
                pass

    async def cog_unload(self):
        # close session on unload
        try:
            if self.session and not self.session.closed:
                await self.session.close()
        except Exception as e:
            print(f"[infoCommands] Error closing session: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCommands(bot))
