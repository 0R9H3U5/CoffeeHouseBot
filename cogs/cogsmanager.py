# cogsmanager.py
"""
Functions for managing cogs.

This file contains what is needed to
load, unload and reload cogs and sync
your commands with discord.

Author: Elcoyote Solitaire

sync command from Umbra:
https://about.abstractumbra.dev/discord.py/2023/01/29/sync-command-example.html
"""
import os
import discord
import json

from typing import Literal, Optional, List
from discord.ext import commands

class Cogsmanager(commands.Cog, name="cogsmanager"):
    """
    Cogs manager.

    This class contains commands to load, unload and
    reload cogs.
    
    Commands:
        !load
        !unload
        !reload
        !showcogs
        !sync
    """
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()

    def load_config(self) -> dict:
        """Load the config.json file."""
        with open('config.json', 'r') as f:
            return json.load(f)

    def get_cog_list(self, cog_name: str) -> List[str]:
        """
        Process the cog_name parameter and return a list of cogs to operate on.
        
        Args:
            cog_name (str): The name of the cog or "all" for all cogs
            
        Returns:
            List[str]: List of cog names to operate on
        """
        if cog_name.lower() == "all":
            # Get all cogs from config, excluding cogsmanager
            return [cog.replace("cogs.", "") for cog in self.config["cogs"] 
                   if cog != "cogs.cogsmanager"]
        return [cog_name]

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx: commands.Context, cog_name: str):
        """
        Loads a specified cog to the bot.

        Args:
            ctx as commands.Context
            cog_name (str): The name of the cog to load or "all" for all cogs.

        Raises:
            commands.ExtensionFailed: If loading the cog fails.
        """
        cogs_to_load = self.get_cog_list(cog_name)
        results = []
        
        for cog in cogs_to_load:
            try:
                await self.bot.load_extension(f"cogs.{cog}")
                results.append(f"✅ {cog} cog has been loaded.")
            except commands.ExtensionFailed as extension_failed:
                results.append(f"❌ Error loading {cog} cog: {extension_failed}")
        
        await ctx.send("\n".join(results))

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, cog_name: str):
        """
        Unloads a specified cog from the bot.

        Args:
            ctx as commands.Context
            cog_name (str): The name of the cog to unload or "all" for all cogs.

        Raises:
            commands.ExtensionNotLoaded: If the specified cog is not loaded.
            commands.ExtensionFailed: If unloading the cog fails.
        """
        cogs_to_unload = self.get_cog_list(cog_name)
        results = []
        
        for cog in cogs_to_unload:
            try:
                await self.bot.unload_extension(f"cogs.{cog}")
                results.append(f"✅ {cog} cog has been unloaded.")
            except commands.ExtensionFailed as extension_failed:
                results.append(f"❌ Error unloading {cog} cog: {extension_failed}")
        
        await ctx.send("\n".join(results))

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, cog_name: str):
        """
        Unloads a specified cog from the bot then loads it back.

        Args:
            ctx as commands.Context
            cog_name (str): The name of the cog to reload or "all" for all cogs.

        Raises:
            commands.ExtensionNotLoaded: If the specified cog is not loaded.
            commands.ExtensionFailed: If reloading the cog fails.
        """
        cogs_to_reload = self.get_cog_list(cog_name)
        results = []
        
        for cog in cogs_to_reload:
            try:
                await self.bot.unload_extension(f"cogs.{cog}")
                await self.bot.load_extension(f"cogs.{cog}")
                results.append(f"✅ {cog} cog has been reloaded.")
            except commands.ExtensionFailed as extension_failed:
                results.append(f"❌ Error reloading {cog} cog: {extension_failed}")
        
        await ctx.send("\n".join(results))

    @commands.command()
    @commands.is_owner()
    async def sync(
        self, ctx: commands.Context, guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        """
        Function to sync commands.

        Please note that using sync takes a few minutes to be fully effective
        on all the bot's servers. To force the sync, use those in order:
        !sync  >>  !sync *  >>  !sync ^

        Examples:
            !sync
                This takes all global commands within the CommandTree
                and sends them to Discord. (see CommandTree for more info.)
            !sync ~
                This will sync all guild commands for the current context's guild.
            !sync *
                This command copies all global commands to the current
                guild (within the CommandTree) and syncs.
            !sync ^
                This command will remove all guild commands from the CommandTree
                and syncs, which effectively removes all commands from the guild.
            !sync 123 456 789
                This command will sync the 3 guild ids we passed: 123, 456 and 789.
                Only their guilds and guild-bound commands.

        Args:
            ctx as context
            guilds: guild(s) to sync
            spec: optional with 1 argument only
        """
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} cmds {'globally' if spec is None else 'to current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    @commands.command()
    @commands.is_owner()
    async def showcogs(self, ctx: commands.Context):
        """
        Shows the current cogs loaded.

        Args:
            ctx as commands.Context
        """
        response = ""
        cog_lines_total = 0
        c_cogs = 0
        for cog in self.bot.cogs:
            cog_file = f"{cog}.py"
            extension_file_path = os.path.join("./cogs", cog_file)
            c_cogs += 1
            response += f"{cog} : {cog_lines}\n"

        await ctx.send(
            "List of the loaded cogs:\n"
            f"{response}\n Total: {c_cogs} cogs"
        )

async def setup(bot):
    """
    Loads the cog on start.
    """
    await bot.add_cog(Cogsmanager(bot))