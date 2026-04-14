import json
import csv
import time
import os
from dotenv import load_dotenv
from dota2.client import Dota2Client
from steam.client import SteamClient

# --- 1. ЗАГРУЗКА ОКРУЖЕНИЯ ---
load_dotenv()

STEAM_USERNAME = os.getenv('STEAM_USERNAME')
STEAM_PASSWORD = os.getenv('STEAM_PASSWORD')
INPUT_FILE = os.getenv('PATH_INPUT_MATCHES')
OUTPUT_FILE = os.getenv('PATH_OUTPUT_REPORT')
HERO_MAP_FILE = os.getenv('PATH_HERO_MAP')

with open(HERO_MAP_FILE, 'r', encoding='utf-8') as f:
    hero_map = json.load(f)

client = SteamClient()
dota = Dota2Client(client)


# Сначала логинимся в Steam
@client.on('logged_on')
def start_dota():
    print("✅ Залогинились в Steam, запускаем Dota 2...")
    dota.launch()


# Когда Dota 2 готова (координатор ответил), начинаем работу
@dota.on('ready')
def start_processing():
    print("✅ Координатор Dota 2 готов! Начинаю сбор данных...")

    match_ids = []
    try:
        with open(INPUT_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                match_ids.append(int(row['Match_ID']))
    except Exception as e:
        print(f"❌ Ошибка чтения {INPUT_FILE}: {e}")
        client.disconnect()
        return

    all_results = []

    for m_id in match_ids:
        print(f"📡 Запрашиваю матч: {m_id}...")
        job_id = dota.request_match_details(m_id)
        res = dota.wait_msg(job_id, timeout=15)

        if res and hasattr(res, 'match'):
            m = res.match

            # --- ФИЛЬТРЫ ---
            # Проверяем режим (2 или 16) и количество реальных игроков (10)
            if m.game_mode not in [2, 16] or m.human_players != 10:
                print(f"⏩ Пропускаю матч {m_id}: Неподходящий режим ({m.game_mode}) или игроков < 10")
                continue
            # ----------------

            winner_team = "Radiant" if m.match_outcome == 2 else "Dire"

            for p in m.players:
                team = "Radiant" if p.player_slot < 128 else "Dire"
                all_results.append({
                    "match_id": m_id,
                    "account_id": p.account_id,
                    "team": team,
                    "win": "Yes" if team == winner_team else "No",
                    "nickname": p.player_name if p.player_name else "Anonymous",
                    "hero": hero_map.get(str(p.hero_id), f"Unknown({p.hero_id})"),
                    "kills": p.kills,
                    "deaths": p.deaths,
                    "assists": p.assists
                })
        else:
            print(f"⚠️ Матч {m_id} не ответил (Timeout)")

        time.sleep(2)  # Увеличил паузу для стабильности

    if all_results:
        keys = all_results[0].keys()
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_results)
        print(f"🚀 Красота! Данные в {OUTPUT_FILE}")
    else:
        print("📭 Ничего не собрали.")

    print("Выходим...")
    dota.exit()
    client.disconnect()


client.cli_login(username=STEAM_USERNAME, password=STEAM_PASSWORD)
client.run_forever()