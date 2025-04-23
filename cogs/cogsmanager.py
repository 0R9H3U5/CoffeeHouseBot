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
import traceback

from typing import Literal, Optional, List
from discord.ext import commands

class Cogsmanager(commands.Cog, name="cogsmanager"):
    """
    Logic for managing cogs
    """
    def __init__(self, bot):
        self.bot = bot

    async def check_leaders_category(self, ctx: commands.Context) -> bool:
        """
        Check if the command is being used in a channel within the LEADERS category
        """
        return await self.bot.get_cog("BaseCog").check_category(
            ctx,
            "LEADERS"
        )

    def get_cog_list(self, cog_name: str) -> list:
        """
        Get a list of cogs to load/unload/reload
        
        Args:
            cog_name: The name of the cog or "all" for all cogs
            
        Returns:
            list: A list of cog names
        """
        if cog_name.lower() == "all":
            # Get all .py files in the cogs directory
            return [f[:-3] for f in os.listdir("cogs") if f.endswith(".py") and not f.startswith("__")]
        else:
            return [cog_name]

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx: commands.Context, cog_name: str):
        if not await self.check_leaders_category(ctx):
            return
            
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
        if not await self.check_leaders_category(ctx):
            return
            
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
        if not await self.check_leaders_category(ctx):
            return
            
        """
        Reloads a specified cog in the bot.

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
                await self.bot.reload_extension(f"cogs.{cog}")
                results.append(f"✅ {cog} cog has been reloaded.")
            except commands.ExtensionFailed as extension_failed:
                results.append(f"❌ Error reloading {cog} cog: {extension_failed}")
        
        await ctx.send("\n".join(results))

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        if not await self.check_leaders_category(ctx):
            return
            
        """
        Syncs the bot's commands with Discord.

        Args:
            ctx as commands.Context
        """
        try:
            await self.bot.tree.sync()
            await ctx.send("✅ Commands have been synced.")
        except Exception as e:
            await self.bot.get_cog("BaseCog").handle_error(ctx, e)

    @commands.command()
    @commands.is_owner()
    async def showcogs(self, ctx: commands.Context):
        if not await self.check_leaders_category(ctx):
            return
            
        """
        Shows all loaded cogs.

        Args:
            ctx as commands.Context
        """
        cogs = [cog for cog in self.bot.cogs.keys()]
        await ctx.send(f"Loaded cogs: {', '.join(cogs)}")

async def setup(bot):
    """
    Loads the cog on start.
    """
    await bot.add_cog(Cogsmanager(bot))