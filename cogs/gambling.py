from collections import Counter
from discord import app_commands
import discord
from discord.ext import commands
from random import *
from datetime import datetime
import asyncio
import aiosqlite
import hashlib
import time

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = bot.db_path
        self.hash_seed = ["보이지 않는 바람에 무거운 연을 띄우며, 얽혀가는 실을 붙잡고 끝내 허공을 헤맨다.", "성에 갇힌 자는 매일 밤 정을 깎아내며 붉은 화를 피운다.", "깊은 병에 고인 수를 마시며, 하염없이 저무는 해를 삼킨다."]

    async def itIsOk(self, ctx, user_id, bet_money : int):
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cur = await conn.execute("SELECT money FROM economy WHERE user_id = ?", (user_id,))
                money = await cur.fetchone()
            if money is None:
                embed = discord.Embed(
                    title='🚨 Error!',
                    description=f'{ctx.author.mention}님은 봇에 가입하지 않았습니다.\n가입 후 다시 시도하십시오.',
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return False, None
            money = money[0]
            if money < bet_money:
                embed = discord.Embed(
                    title = '🚨 Error!',
                    description=f'{ctx.author.mention}님은 돈이 부족합니다.',
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return False, None
            if bet_money < 500 or bet_money is None:
                embed = discord.Embed(
                    title='🚨 Error!',
                    description='배팅할 수 있는 최소 금액은 500원입니다.',
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return False, None
            return True, money
        except Exception as e:
            print(f"Error in itIsOk: {e}")
            return False, None

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏱️ 너무 빠릅니다! {error.retry_after:.2f}초 후 다시 시도하세요.", ephemeral=True)
        elif isinstance(error, (commands.BadArgument, commands.MissingRequiredArgument)):
            await ctx.send("🚨 배팅 금액을 숫자로 정확히 입력해주세요.", ephemeral=True)

    @commands.hybrid_command(name = '슬롯머신', aliases=['slots'], description="돈을 걸고 슬롯머신을 돌립니다.")
    @app_commands.rename(bet = '금액')
    @discord.app_commands.describe(bet="배팅할 금액을 입력하세요.")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def slot_machine(self, ctx, bet : int):
        user = ctx.author
        isOk, money = await self.itIsOk(ctx, user.id, bet)
        if not isOk: return
        async with aiosqlite.connect(self.db_path, timeout=10) as conn:
            await conn.execute("UPDATE economy SET money = money - ? WHERE user_id = ?", (bet, user.id))
            await conn.commit()
        icons = '🔴🟠🟡🟢🔵🟣🟤⚫⚪⚜️'
        icon = ['❔','❔','❔','❔','❔']
        embed = discord.Embed(
            title = 'Slot Machine',
            description = f'# {" ".join(icon)}',
            color = discord.Color.light_grey()
        )
        embed.set_footer(text=f'🎰 Casino')
        embed.timestamp = datetime.now()
        msg = await ctx.send(embed=embed)
        icon_r=[randint(0,9) for _ in range(5)]
        for i in range(5):
            await asyncio.sleep(0.6)
            icon[i] = icons[icon_r[i]]
            embed.description = f"# {' '.join(icon)}"
            if i==4: embed.color = discord.Color.gold()
            await msg.edit(embed=embed)
        counts = Counter(icon_r)
        match_emoji_id, match_count = counts.most_common(1)[0]
        match_emoji = icons[match_emoji_id]
        if match_count == 5:
            power,msgs = 777, '🥳 Jackpot!'
        elif match_count == 4:
            power,msgs = 50, f'💎 Nice! 4 correct!'
        elif match_count == 3:
            power,msgs = 3, f'😊 Good! 3 correct!'
        elif match_count == 2:
            power,msgs = 0.65, f'⚖️ Hmm...'
        else:
            power,msgs = 0, f'😭 Fail...'
        reward = int(bet * power)
        async with aiosqlite.connect(self.db_path, timeout=10) as conn:
            cur = await conn.execute("UPDATE economy SET money = money + ? WHERE user_id = ?", (reward, user.id))
            k = await conn.execute("SELECT money FROM economy WHERE user_id = ?", (user.id,))
            money = (await k.fetchone())[0]
            await conn.commit()
        embed.add_field(name = '아이콘', value=f'{match_emoji}', inline=True)
        embed.add_field(name = '일치 갯수',value=match_count, inline=True)
        embed.add_field(name = '결과', value=f'{msgs}', inline=True)
        embed.add_field(name = '수익', value=f'{reward:,}원', inline=True)
        embed.add_field(name = '잔고', value=f'{money:,}원', inline=False)
        await msg.edit(embed=embed)
    
    @commands.hybrid_command(name = '경마', aliases=['horse_racing'], description='어느 말이 존@나 빠른가에 대하여 돈을 걸고 싸웁니다.')
    @app_commands.rename(bet = '금액',horses = '말')
    @discord.app_commands.describe(bet="배팅할 금액을 입력하세요.", horses="배팅할 말을 선택하세요.")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def horse_racing(self, ctx, bet : int, horses : app_commands.Range[int, 1, 5]):
        user = ctx.author
        isOk, money = await self.itIsOk(ctx, user.id, bet)
        if not isOk: return
        async with aiosqlite.connect(self.db_path, timeout=10) as conn:
            await conn.execute("UPDATE economy SET money = money - ? WHERE user_id = ?", (bet, user.id))
            await conn.commit()
        horses_going = ['🐎','🐎','🐎','🐎','🐎']
        horse_gone = [0,0,0,0,0]
        tracks = [f'{i+1}번 말: {horses_going[i]}{"-"*20}|' for i, h in enumerate(horses_going)]
        embed = discord.Embed(
            title = 'Horse Racing',
            description='\n'.join(tracks),
            color = discord.Color.light_grey()
        )
        embed.set_footer(text=f'🎰 Casino')
        embed.timestamp = datetime.now()
        msg = await ctx.send(embed=embed)
        while max(horse_gone) < 20:
            horse_gones = [randint(1,5) for _ in range(5)]
            for i in range(5):
                horse_gone[i] = min(20, horse_gone[i] + horse_gones[i])
                horses_going[i] = f"-" * horse_gone[i] + '🐎' + "-" * (20-horse_gone[i]) + "|"
                tracks[i] = f'{i+1}번 말: {horses_going[i]}'
            embed.description = '\n'.join(tracks)
            await msg.edit(embed=embed)
            await asyncio.sleep(1.2)
        winners = [i+1 for i,pos in enumerate(horse_gone) if pos == 20]
        winners_str = ", ".join(map(str, winners))
        embed.add_field(name='우승마', value=f'{winners_str}번 말', inline=True)
        await msg.edit(embed=embed)
        if horses in winners:
            if len(winners) > 1:
                power = max(1.5, 4/len(winners))
                win_message = f'🥳 {horses}번 말이 공동 우승했습니다! (동착으로 인해 수익이 분배되었습니다.)'
            else:
                power = 4
                win_message = f'🥳 {horses}번 말이 우승했습니다!'
        else:
            power,win_message = 0,f'😭 {horses}번 말이 우승하지 못했습니다...'
        reward = int(bet * power)
        async with aiosqlite.connect(self.db_path, timeout=10) as conn:
            await conn.execute("UPDATE economy SET money = money + ? WHERE user_id = ?", (reward, user.id))
            k = await conn.execute("SELECT money FROM economy WHERE user_id = ?", (user.id,))
            money = (await k.fetchone())[0]
            await conn.commit()
        embed.add_field(name='수익', value=f'{reward:,}원', inline=True)
        embed.add_field(name='결과', value=win_message, inline=False)
        embed.add_field(name='잔고', value=f'{money:,}원', inline=False)
        embed.color = discord.Color.gold() if power != 0 else discord.Color.red()
        await msg.edit(embed=embed)
    
    @commands.hybrid_command(name = '달팽이레이싱', aliases=['snail_racing', '달팽이'], description='어느 변덕쟁이 달팽이가 존@나 빠른가를 두고 싸웁니다.')
    @app_commands.rename(bet = '금액',snails = '달팽이')
    @discord.app_commands.describe(bet="배팅할 금액을 입력하세요.", snails="배팅할 달팽이를 선택하세요.")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def snail_racing(self, ctx, bet : int, snails : app_commands.Range[int, 1, 5]):
        user = ctx.author
        isOk, money = await self.itIsOk(ctx, user.id, bet)
        if not isOk: return
        async with aiosqlite.connect(self.db_path, timeout=10) as conn:
            await conn.execute("UPDATE economy SET money = money - ? WHERE user_id = ?", (bet, user.id))
            await conn.commit()
        snails_going = ['🐌','🐌','🐌','🐌','🐌']
        snail_gone = [0,0,0,0,0]
        tracks = [f'{i+1}번 달팽이: {snails_going[i]}{"-"*10}|' for i, h in enumerate(snails_going)]
        embed = discord.Embed(
            title = 'Snail Racing',
            description='\n'.join(tracks),
            color = discord.Color.light_grey()
        )
        embed.set_footer(text=f'🎰 Casino')
        embed.timestamp = datetime.now()
        msg = await ctx.send(embed=embed)
        while max(snail_gone) < 10:
            snail_gones = [randint(-1,2) for _ in range(5)]
            for i in range(len(tracks)):
                snail_gone[i] = max(0, min(10, snail_gone[i] + snail_gones[i]))
                snails_going[i] = f"-" * snail_gone[i] + '🐌' + "-" * (10-snail_gone[i]) + "|"
                tracks[i] = f'{i+1}번 달팽이: {snails_going[i]}'
            embed.description = '\n'.join(tracks)
            await msg.edit(embed=embed)
            await asyncio.sleep(1.5)
        winners = [i+1 for i,pos in enumerate(snail_gone) if pos == 10]
        winners_str = ", ".join(map(str, winners))
        embed.add_field(name='우승한 달팽이', value=f'{winners_str}번 달팽이', inline=True)
        await msg.edit(embed=embed)
        if snails in winners:
            if len(winners) > 1:
                power,win_message = max(1.25, 3.5/len(winners)),f'🥳 {snails}번 달팽이가 공동 우승했습니다! (동착으로 인해 수익이 분배되었습니다.)'
            else: power,win_message = 3.5,f'🥳 {snails}번 달팽이가 우승했습니다!'
        else:
            power,win_message = 0,f'😭 {snails}번 달팽이가 우승하지 못했습니다...'
        reward = int(bet * power)
        async with aiosqlite.connect(self.db_path, timeout=10) as conn:
            await conn.execute("UPDATE economy SET money = money + ? WHERE user_id = ?", (reward, user.id))
            k = await conn.execute("SELECT money FROM economy WHERE user_id = ?", (user.id,))
            money = (await k.fetchone())[0]
            await conn.commit()
        embed.add_field(name='수익', value=f'{reward:,}원', inline=True)
        embed.add_field(name='결과', value=win_message, inline=False)
        embed.add_field(name='잔고', value=f'{money:,}원', inline=False)
        embed.color = discord.Color.green() if power != 0 else discord.Color.red()
        await msg.edit(embed=embed)
        
    @commands.hybrid_command(name = '홀짝', aliases=['even_odd'], description='해시된 무작위 난수가 짝수인지 홀수인지 맞추는 게임입니다.')
    @app_commands.rename(bet = '금액',choice = '선택')
    @discord.app_commands.describe(bet="배팅할 금액을 입력하세요.", choice="홀수인지 짝수인지 선택하세요.")
    @app_commands.choices(choice = [app_commands.Choice(name = '홀', value = '1'),app_commands.Choice(name = '짝', value = '2'),])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def even_odd(self, ctx, bet : int, choice : app_commands.Choice[str]):
        user = ctx.author
        isOk, money = await self.itIsOk(ctx, user.id, bet)
        if not isOk: return
        
        async with aiosqlite.connect(self.db_path, timeout=10) as conn:
            await conn.execute("UPDATE economy SET money = money - ? WHERE user_id = ?", (bet, user.id))
            await conn.commit()

        hasing_target = f'{time.time_ns()}#{user.id}#{self.hash_seed[randint(0,2)]}'
        hasing_result = hashlib.sha1(hasing_target.encode('utf-8')).hexdigest()
        hasing_result_int = int(hasing_result, 16)
        
        # 짝(2) -> %2 == 0, 홀(1) -> %2 == 1
        is_even = hasing_result_int % 2 == 0
        win = (is_even and choice.value == "2") or (not is_even and choice.value == "1")
        
        if win:
            reward = int(bet * 1.95)
        else:
            reward = 0
        async with aiosqlite.connect(self.db_path, timeout=10) as conn:
            await conn.execute("UPDATE economy SET money = money + ? WHERE user_id = ?", (reward, user.id))
            k = await conn.execute("SELECT money FROM economy WHERE user_id = ?", (user.id,))
            money = (await k.fetchone())[0]
            await conn.commit()
        embed = discord.Embed(
            title = '홀짝',
            description = f'{user.mention}님이 {bet:,}원을 배팅했습니다.',
            color = discord.Color.light_grey()
        )
        embed.set_footer(text=f'🎰 Casino')
        embed.timestamp = datetime.now()
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(0.5)
        if win:
            embed.add_field(name='결과', value=f'**{choice.name}**을(를) 선택하셨습니다. 승리했습니다!', inline=False)
            embed.color = discord.Color.green()
        else:
            embed.add_field(name='결과', value=f'**{choice.name}**을(를) 선택하셨습니다. 패배했습니다...', inline=False)
            embed.color = discord.Color.red()
        embed.add_field(name='수익', value=f'{reward:,}원', inline=True)
        embed.add_field(name='잔고', value=f'{money:,}원', inline=True)
        embed.add_field(name = '해시 결과', value=f'`0x{hasing_result}`', inline=False)
        await msg.edit(embed=embed)
    
    @commands.hybrid_command(name = '주사위', aliases=['dice'], description='주사위 2개의 합을 맞추는 게임입니다.')
    @app_commands.rename(bet = '금액',choice = '선택')
    @discord.app_commands.describe(bet="배팅할 금액을 입력하세요.", choice="합이 얼마인지 고르세요.")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def dice(self, ctx, bet : int, choice : app_commands.Range[int, 2, 12]):
        user = ctx.author
        ok, money = await self.itIsOk(ctx, user.id, bet)
        if not ok: return

        dices = [randint(1,6) for _ in range(2)]
        sums = sum(dices)
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("UPDATE economy SET money = money - ? WHERE user_id = ?", (bet, user.id))
            await conn.commit()
        
        embed = discord.Embed(
            title = '주사위',
            description = f'{user.mention}님이 {bet:,}원을 배팅했습니다.',
            color = discord.Color.light_grey()
        )
        embed.set_footer(text=f'🎰 Casino')
        embed.timestamp = datetime.now()
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(0.5)
        embed.add_field(name='주사위', value=f'{dices[0]} + {dices[1]} = ', inline=True)
        await msg.edit(embed=embed)
        await asyncio.sleep(0.5)
        embed.clear_fields()
        embed.add_field(name='주사위', value=f'{dices[0]} + {dices[1]} = {sums}', inline=True)
        await msg.edit(embed=embed)

        if sums == choice:
            reward = int(bet * 4)
            result_text = f'주사위가 {choice}와 일치합니다! 축하합니다! 🥳'
        else:
            reward = 0
            result_text = f'주사위가 {choice}와 일치하지 않습니다... 아쉽네요 😭'
        async with aiosqlite.connect(self.db_path, timeout=10) as conn:
            await conn.execute("UPDATE economy SET money = money + ? WHERE user_id = ?", (reward, user.id))
            k = await conn.execute("SELECT money FROM economy WHERE user_id = ?", (user.id,))
            current_money = (await k.fetchone())[0]
            await conn.commit()
        embed.add_field(name='결과', value=result_text, inline=False)
        embed.add_field(name='수익', value=f'{reward:,}원', inline=True)
        embed.add_field(name='잔고', value=f'{current_money:,}원', inline=True)
        embed.color = discord.Color.green() if reward != 0 else discord.Color.red()
        await msg.edit(embed=embed)
            
        


async def setup(bot):
    await bot.add_cog(Gambling(bot))