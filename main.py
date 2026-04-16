import aiosqlite
import discord
from discord.ext import commands
import sys
import os
import dotenv
import json

dotenv.load_dotenv()
try:
    with open('settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    with open('admins.json', 'r', encoding='utf-8') as f:
        admins = json.load(f)
except FileNotFoundError:
    print("❌ 설정 파일(settings.json 또는 admins.json)을 찾을 수 없습니다.")
    print("먼저 'python settings.py'를 실행하여 초기 설정을 완료해주세요.")
    sys.exit(1)

async def init_db():
    async with aiosqlite.connect('usersdata.db') as conn:
        await conn.execute("CREATE TABLE IF NOT EXISTS economy (user_id TEXT PRIMARY KEY, money INTEGER, bank_code INTEGER, gold_bar INTEGER)")
        await conn.execute("CREATE TABLE IF NOT EXISTS vault (user_id TEXT PRIMARY KEY, money INTEGER, gold_bar INTEGER, FOREIGN KEY (user_id) REFERENCES economy(user_id) ON DELETE CASCADE)")
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.commit()
    async with aiosqlite.connect('usersdata.db') as conn:
        await conn.execute("INSERT OR IGNORE INTO economy (user_id, money, bank_code, gold_bar) VALUES (1483721236289814568, 15000000, NULL, 2500)")
        await conn.commit()

intents = discord.Intents.default()
intents.message_content = True

# 설정값 가져오기
status_str = settings.get('status', 'online')
prefix = settings.get('prefix', '!')

# 상태 맵핑
status_map = {
    'idle': discord.Status.idle,
    'dnd': discord.Status.dnd,
    'offline': discord.Status.offline,
    'online': discord.Status.online,
    'playing': discord.Status.online
}

current_status = status_map.get(status_str, discord.Status.online)
current_activity = None

if status_str == 'playing':
    current_activity = discord.Game(name=settings.get('activity', '봇 작동 중'))

bot = commands.Bot(
    command_prefix=prefix,
    intents=intents,
    status=current_status,
    activity=current_activity
)

bot.db_path = 'usersdata.db'

# 관리자 ID를 숫자로 변환하여 저장
allowed = [int(i) for i in admins.get('admins', [])]


def is_allowed():
    async def predicate(ctx):
        return ctx.author.id in allowed
    return commands.check(predicate)

@bot.event
async def on_ready():
    await init_db()
    print('- 다음으로 로그인되었습니다.', bot.user.name, bot.user.id, sep='\n -')


async def setup_hook():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            extension = f'cogs.{filename[:-3]}'
            try:
                await bot.load_extension(extension)
            except commands.ExtensionAlreadyLoaded:
                pass
            except Exception as e:
                print(f"❌ '{extension}' 모듈 로드 중 오류 발생: {e}")
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            extension = f'cogs.{filename[:-3]}'
            try:
                await bot.load_extension(extension)
            except Exception as e:
                print(f"❌ '{extension}' 모듈 로드 중 오류 발생: {e}")
                
bot.setup_hook = setup_hook
    
@bot.hybrid_command(name='sql_command', aliases=['sql'])
@is_allowed()
@discord.app_commands.describe(command="실행할 SQL 명령어")
async def sql_command(ctx, *,command):
    try:
        async with aiosqlite.connect(bot.db_path) as conn:
            cur = await conn.execute(command)
            result = await cur.fetchall()
            await conn.commit()
        if result:
            result_t = "\n".join([str(row) for row in result])
            await ctx.send(f"✅ SQL 명령이 성공적으로 전송되었습니다.\n```sql\n{result_t[:1950]}\n```")
        else:
            await ctx.send(f"✅ SQL 명령이 성공적으로 전송되었습니다.\n```반환된 값이 존재하지 않습니다.```")
    except Exception as e:
        await ctx.send(f"❌ SQL 명령 실행 중 오류 발생: {e}")


@bot.hybrid_command(name='test', aliases=['테스트'], description="봇의 상태를 테스트합니다.")
@commands.has_permissions(administrator=True)
async def testing(ctx):
    await ctx.send(f'{ctx.author.mention}님. 봇이 정상적으로 동작하고 있습니다.')

@bot.command(name='cog_r', aliases=['모듈_재시동'])
@is_allowed()
async def cog_restart(ctx, extension):
    message = await ctx.send('모듈을 재시동하고 있습니다.')
    if extension.lower() == 'all':
        extension = list(bot.extensions.keys())
        reloaded_list = []
        error_list = []

        for ext in extension:
            try:
                await bot.reload_extension(ext)
                reloaded_list.append(ext.split('.')[-1])
            except Exception as e:
                error_list.append(f"{ext.split('.')[-1]}: {e}")
        
        status_msg = f"✅ {len(reloaded_list)}개 모듈 재로드 성공"
        if error_list:
            status_msg += f"\n❌ **오류 발생:**\n" + "\n".join(error_list)
        
        await message.edit(content=status_msg)
        return
    try:
        await bot.reload_extension(f'cogs.{extension}')
        await message.edit(content = f"✅ '{extension}' 모듈이 성공적으로 재로드되었습니다.")
    except commands.ExtensionNotLoaded:
        # 만약 로드가 안 되어 있다면 새로 로드 시도
        try:
            await bot.load_extension(f'cogs.{extension}')
            await message.edit(content=f"📥 '{extension}' 모듈이 새로 로드되었습니다.")
        except Exception as e:
            await message.edit(content = f"❌ 재로드 중 오류 발생: {e}")
    except Exception as e:
        await message.edit(content = f"❌ 재로드 중 오류 발생: {e}")

@bot.command(name='reboot')
@is_allowed()
async def reboot(ctx):
    await ctx.send("🔄 봇 시스템을 재시동하겠습니다.\n봇의 모든 기능이 일시적으로 중단되며, 서비스를 다시 로딩해야 할수도 있습니다.")
    os.execv(sys.executable,[sys.executable] + sys.argv)

@bot.command(name='exit')
@is_allowed()
async def exit(ctx):
    await ctx.send("🔚 봇 시스템이 종료됩니다.")
    await bot.close()
    quit()

@bot.command(name='sync')
@is_allowed()
async def sync(ctx):
    msg = await ctx.send("🔄 슬래시 명령어를 동기화 중입니다...")
    try:
        synced = await bot.tree.sync()
        await msg.edit(content=f"✅ {len(synced)}개의 슬래시 명령어가 동기화되었습니다.")
    except Exception as e:
        await msg.edit(content=f"❌ 동기화 중 오류 발생: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title = '❌ 거부됨',
            description=f'해당 명령어를 이용할 권한이 없습니다.',
            color = discord.Color.brand_red()
        )
        await ctx.send(embed=embed);
    elif isinstance(error, commands.CommandNotFound):
        print('앙')
    elif isinstance(error, commands.ExtensionAlreadyLoaded):
        pass # 이미 로드된 경우 조용히 넘어감
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title = '⚠️ 오류',
            description=f'명령어가 요구하는 필수 인자값이 누락되었습니다.\n명령어를 확인하고, 다시 입력해주십시오.',
            color = discord.Color.brand_red()
        )
        await ctx.send(embed=embed)
    else:
        print(f'Errors! : {error}')

token = os.getenv('BOT_TOKEN')

bot.run(token)