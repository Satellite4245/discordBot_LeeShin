import aiosqlite
import discord
from discord.ext import commands
from datetime import datetime
import asyncio
import time

class test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = bot.db_path

    @commands.command(name='test_color')
    async def test(self, ctx):
        user = ctx.message.author
        embed = discord.Embed(
            title = 'Test',
            description='Test',
            color = discord.Color.og_blurple()
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(test(bot))