import os

os.system('pip install -r requirements.txt')

import time
from rich import *
from rich.panel import *
from rich.prompt import *
import dotenv
import json
import hashlib

env_file = '.env'

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

clear()
clear()

print(Panel("""
[bold cyan] 반갑습니다! [/bold cyan]

먼저, 봇의 실행을 위하여, 토큰이 필요합니다.
"""))
token = Prompt.ask("[bold yellow]봇 토큰을 입력하세요\n -> [/bold yellow]", password=True)
dotenv.set_key(env_file, 'BOT_TOKEN', token)

print(Panel(f"""
[bold green]토큰이 성공적으로 저장되었습니다![/bold green]

3초후 계속됩니다...
"""))
time.sleep(3)

clear()

print(Panel(f"""
[bold cyan]이제, 관리자 권한을 설정하겠습니다.[/bold cyan]

디스코드 유저 id, 관리자 페이지에서 이용한 ID와 비밀번호가 필요합니다.
"""
))
admin_discord = Prompt.ask("[bold sky_blue1]관리자의 디스코드 숫자 id를 입력해주십시오.\n -> [/bold sky_blue1]")
admin_id = Prompt.ask("[bold sky_blue1]관리자 페이지 id를 입력해주십시오.\n -> [/bold sky_blue1]")
admin_pw = Prompt.ask("[bold red]관리자 페이지 비밀번호를 입력해주십시오.\n -> [/bold red]", password=True)

with open('admins.json', 'w', encoding='utf-8') as f:
    json.dump({
        "admins": [
            admin_discord
        ],
        "id": admin_id,
        "password": hashlib.sha256(admin_pw.encode()).hexdigest()
    }, f, indent=4, ensure_ascii=False)


print(Panel(f"""
[bold green]관리자 권한이 설정되었습니다![/bold green]

3초후 계속됩니다...
"""))
time.sleep(3)
clear()

print(Panel("""
[bold cyan]봇 세부 설정[/bold cyan]

이제, 봇의 세부 설정을 진행하겠습니다.
아래의 항목을 확인하십시오.

1. 봇의 접두사
2. 봇의 활동 상태
"""))

prefix = Prompt.ask("[bold yellow]봇의 접두사를 입력해주세요\n -> [/bold yellow]")
status = Prompt.ask("[bold yellow]봇의 활동 상태를 입력해주세요\n -> [/bold yellow]", choices=['online', 'idle', 'dnd', 'offline', 'playing'], default='online')
if status == 'playing':
    activity = Prompt.ask("[bold yellow]봇의 활동 내용을 입력해주세요\n -> [/bold yellow]")
else:
    activity = None


print(Panel(f"""
[bold green]거의 끝났습니다![/bold green]

3초후 계속됩니다...
"""))
time.sleep(3)
clear()

print(Panel("""
[bold cyan]이제, 마지막으로 다음에 서약하셔야 합니다.[/bold cyan]

[bold cornflower_blue]서비스 이용약관[/bold cornflower_blue]

1. 해당 디스코드 봇 및 이를 기반으로 상업적인 이익, 이득을 취할 수 없습니다.
2. 디스코드의 서비스 약관(ToS)를 준수하여야 합니다.
3. 일련의 도박 등의 게임은 '가상의 화폐'로 진행되며, 이를 실제 현금으로 환전, 거래, 교환할 수 없습니다.
4. 이용중 도박 중독 등에 각별히 유의하시길 바랍니다.
"""))

confirm = Prompt.ask("[bold yellow]동의하십니까?\n -> [/bold yellow]", choices=["y", "n"], default='y', show_choices=True)

if confirm == 'n':
    clear()
    print(Panel("[bold red]동의하지 않으셨습니다. 프로그램을 종료합니다.[/bold red]"))
    exit()

with open('settings.json', 'w', encoding='utf-8') as f:
    json.dump({
        "prefix": prefix,
        "status": status,
        "activity": activity
    }, f, indent=4, ensure_ascii=False)

print(Panel("[bold green] 모든 설정이 성공적으로 완료되었습니다! 이제 이용하셔도 좋습니다! [/bold green]"))
