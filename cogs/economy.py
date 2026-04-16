import aiosqlite
import discord
from discord.ext import commands
from datetime import datetime
import asyncio
import time

bank = ['🏦 조선은행']

class RegisterView(discord.ui.View):
    def __init__(self, bot, db_path):
        super().__init__(timeout=60)
        self.bot = bot
        self.db_path = db_path

    @discord.ui.button(label='가입하기', style=discord.ButtonStyle.primary, emoji='✅', custom_id='gaip')
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            user = interaction.user
            async with aiosqlite.connect(self.db_path) as conn:
                cur = await conn.execute("SELECT 1 FROM economy WHERE user_id = ?", (str(user.id),))
                eme = await cur.fetchone() is not None
            
            if eme:
                embed = discord.Embed(
                    title = 'Error!',
                    description=f'{user.mention}님은 이미 가입되어 있습니다.\n봇의 대부분의 기능을 이용하실 수 있습니다.',
                    color=discord.Color.red()
                )
            else:
                try:
                    async with aiosqlite.connect(self.db_path) as conn:
                        await conn.execute("INSERT INTO economy VALUES (?, 150000, 0, 0)", (str(user.id),))
                        await conn.commit()
                    embed= discord.Embed(
                        title = '환영합니다.',
                        description=f'{user.mention}님 환영합니다. 가입이 완료되었습니다.\n',
                        color = discord.Color.brand_green()
                        )
                except Exception as e:
                    embed = discord.Embed(
                        title = 'Error!',
                        description=f'{user.mention}님, 가입 중 문제가 발생하여 가입이 거부되었습니다.\n오류가 개발자에게 보고되었습니다. 잠시후 다시 시도하십시오.',
                        color=discord.Color.red()
                    )
                    channel_id = 1483721236289814568
                    report_channel = self.bot.get_channel(channel_id)
                    if report_channel:
                        c_embed = discord.Embed(
                            title = '오류 보고',
                            description=f'{user}({user.id})님이 가입 중 오류가 발생했습니다.',
                            timestamp=datetime.now(),
                            color = discord.Color.dark_red()
                        )
                        c_embed.add_field(name='발생시각',value=f'<t:{int(time.time())}:F>',inline=False)
                        c_embed.add_field(name='오류 내용', value=f'```py\n{e}\n```',inline=False)
                        await report_channel.send(embed=c_embed)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.message.delete()
        except Exception as e:
            print(f"Error in register button: {e}")

    @discord.ui.button(label = '취소', style=discord.ButtonStyle.secondary, custom_id='cancel')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = bot.db_path

    async def check(self, id):
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.execute("SELECT 1 FROM economy WHERE user_id = ?", (id,))
            return await cur.fetchone() is not None

    @commands.hybrid_command(name='register', aliases=['가입'], description="봇의 시스템에 가입합니다.")
    async def register(self, ctx):
        try:
            user = ctx.author
            if await self.check(str(user.id)):
                embed = discord.Embed(
                    title = 'Error!',
                    description=f'{user.mention}님은 이미 가입되어 있습니다.\n봇의 대부분의 기능을 이용하실 수 있습니다.',
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed, ephemeral=True)
                return
            
            view = RegisterView(self.bot, self.db_path)
            embed = discord.Embed(
                title = "가입하시겠습니까?",
                description="봇에 가입하시면 개인정보처리방침에 동의함으로 간주하고, 사용자님의 ID를 기록합니다.",
                color=discord.Color.og_blurple()
            )
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            print(f"Error in register command: {e}")

    @commands.hybrid_command(name='balance', aliases=['잔고','잔액','ㄷ'], description="현재 자신의 잔고와 금 보유 현황을 확인합니다.")
    async def remain_money(self, ctx):
        try:
            user = ctx.author
            if not await self.check(str(user.id)):
                embed = discord.Embed(
                    title = 'Error!',
                    description=f'{user.mention}님은 가입되어 있지 않습니다.\n.register 명령어를 통해 가입해주세요.',
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            async with aiosqlite.connect(self.db_path) as conn:
                cur = await conn.execute("SELECT * FROM economy WHERE user_id = ?", (str(user.id),))
                row = await cur.fetchone()
            money = row[1]
            bank_code = row[2]
            golds = row[3]
            embed = discord.Embed(
                title = f'{user.display_name}님의 통장',
                description="⚠️ 금고에 보관하지 않은 자산에는 세금이 부과됩니다!",
                color = discord.Color.og_blurple()
            )
            embed.add_field(name = '잔고', value = f'{money:,}원', inline = True)
            embed.add_field(name = '금', value=f'{golds:,}돈', inline= True)
            embed.set_footer(text=bank[bank_code])
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error in balance command: {e}")

    # @commands.hybrid_command(name = '입금', aliases=['조회'], description="다른 유저의 잔고와 금 보유 현황을 조회합니다.")
    # @discord.app_commands.describe(user="조회할 유저를 선택하세요.")
    

    @commands.hybrid_command(name = 'balance_search', aliases=['조회'], description="다른 유저의 잔고와 금 보유 현황을 조회합니다.")
    @discord.app_commands.describe(user="조회할 유저를 선택하세요.")
    async def balance_search(self, ctx, user: discord.Member):
        try:
            if not await self.check(str(user.id)):
                embed = discord.Embed(
                    title = 'Error!',
                    description=f'{user.mention}님은 가입되어 있지 않습니다.\n.register 명령어를 통해 가입해주세요.',
                    color=discord.Color.red()
                )
                embed.timestamp = datetime.now()
                await ctx.send(embed=embed)
                return
            async with aiosqlite.connect(self.db_path) as conn:
                cur = await conn.execute("SELECT * FROM economy WHERE user_id = ?", (str(user.id),))
                row = await cur.fetchone()
            money = row[1]
            bank_code = row[2]
            golds = row[3]
            embed = discord.Embed(
                title = f'{user.display_name}님의 통장',
                description="⚠️ 금고에 보관하지 않은 자산에는 세금이 부과됩니다!",
                color = discord.Color.og_blurple()
            )
            embed.add_field(name = '잔고', value = f'{money:,}원', inline = True)
            embed.add_field(name = '금', value=f'{golds:,}돈', inline= True)
            embed.timestamp = datetime.now()
            embed.set_footer(text=bank[bank_code])
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error in balance_search command: {e}")
    @commands.hybrid_command(name = '잔돈싫어', aliases=['throw'], description="1천원 이하의 잔돈을 버릴 수 있습니다.")
    @discord.app_commands.describe(money="버릴 금액을 입력하세요.")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def jandon_sileo(self, ctx, money: int):
        user = ctx.author
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.execute("SELECT money FROM economy WHERE user_id = ?", (str(user.id),))
            row = await cur.fetchone()
        if row is None:
            embed = discord.Embed(
                title = '🚨 Error!',
                description=f'{ctx.author.mention}님은 봇에 가입하지 않았습니다.\n가입 후 다시 시도하십시오.',
                color = discord.Color.red()
            )
            embed.set_footer(text="🗑️ 쓰레기통")
            embed.timestamp = datetime.now()
            await ctx.send(embed = embed)
            return
        row = row[0]
        if row < money:
            embed = discord.Embed(title='🚨 Error!', description='버릴 돈이 부족합니다.', color=discord.Color.red())
            embed.set_footer(text="🗑️ 쓰레기통")
            embed.timestamp = datetime.now()
            await ctx.send(embed=embed)
            return
        if money > 1000:
            embed = discord.Embed(
                title = '🚨 Error!',
                description='1천원 이상은 버릴수 없습니다!\n||👵🏻 - 땅을 파봐라 돈이 나오냐?||',
                color = discord.Color.red()
            )
            embed.set_footer(text="🗑️ 쓰레기통")
            embed.timestamp = datetime.now()
            await ctx.send(embed = embed)
            return
        if money < -1000:
            embed = discord.Embed(
                title = '🚨 Error!',
                description='-1000원 이하는 버릴수 없습니다!\n||👵🏻 - 땅을 파봐라 돈이 나오냐?||',
                color = discord.Color.red()
            )
            embed.set_footer(text="🗑️ 쓰레기통")
            embed.timestamp = datetime.now()
            await ctx.send(embed = embed)
            return
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("UPDATE economy SET money = money - ? WHERE user_id = ?", (money, user.id))
            await conn.commit()
        embed = discord.Embed(
            title = '🗑️ 쓰레기통',
            description=f'{user.mention}님이 {money:,}원을 버렸습니다.',
            color = discord.Color.og_blurple()
        )
        embed.set_footer(text="🗑️ 쓰레기통")
        embed.timestamp = datetime.now()
        await ctx.send(embed = embed)
    @jandon_sileo.error
    async def jandon_sileo_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title = '🚨 Error!',
                description=f'너무 여러번 버리고 있습니다!\n{error.retry_after:.2f}초후에 다시 시도하십시오.',
                color = discord.Color.red()
            )
            embed.set_footer(text="🗑️ 쓰레기통")
            embed.timestamp = datetime.now()
            await ctx.send(embed = embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title = '🚨 Error!',
                description=f'버릴 금액을 입력해주세요.',
                color = discord.Color.red()
            )
            embed.set_footer(text="🗑️ 쓰레기통")
            embed.timestamp = datetime.now()
            await ctx.send(embed = embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title = '🚨 Error!',
                description='버릴 금액은 숫자로 입력해야해요!',
                color = discord.Color.red()
            )
            embed.set_footer(text="🗑️ 쓰레기통")
            embed.timestamp = datetime.now()
            await ctx.send(embed = embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))