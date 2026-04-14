import json
import csv
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from dota2.client import Dota2Client
from steam.client import SteamClient

# --- НАСТРОЙКИ ---
load_dotenv()
# --- В начале скрипта ---
STEAM_USERNAME = os.getenv('STEAM_USERNAME')
STEAM_PASSWORD = os.getenv('STEAM_PASSWORD')
USER_DIR = os.path.join('data', STEAM_USERNAME)
INPUT_FILE = os.path.join(USER_DIR, 'matches.csv')
OUTPUT_FILE = os.path.join(USER_DIR, 'analytics_report.csv')
HERO_MAP_FILE = os.getenv('PATH_HERO_MAP')

with open(HERO_MAP_FILE, 'r', encoding='utf-8') as f:
    hero_map = json.load(f)

client = SteamClient()
dota = Dota2Client(client)


@client.on('logged_on')
def start_dota():
    print(f"✅ Вход в Steam выполнен. Запуск Dota 2...")
    dota.launch()


@dota.on('ready')
def start_processing():
    print("✅ Координатор готов. Начинаю чтение matches.csv...")

    match_ids = []
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Файл {INPUT_FILE} не найден! Сначала запусти prepare_matches.py")
        client.disconnect()
        return

    with open(INPUT_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            match_ids.append(int(row['Match_ID']))

    all_results = []

    for m_id in match_ids:
        print(f"📡 Запрашиваю данные матча: {m_id}...")
        job_id = dota.request_match_details(m_id)
        res = dota.wait_msg(job_id, timeout=15)

        if res and hasattr(res, 'match'):
            m = res.match

            # Фильтрация (на всякий случай, если в matches.csv попало лишнее)
            if m.game_mode not in [2, 16] or m.human_players != 10:
                continue

            winner_team = "Radiant" if m.match_outcome == 2 else "Dire"

            # --- РАБОТА С ДАТОЙ ---
            # m.startTime — это Unix Timestamp. Превращаем в формат ГГГГ-ММ-ДД ЧЧ:ММ
            readable_date = datetime.fromtimestamp(m.startTime).strftime('%Y-%m-%d %H:%M')

            for p in m.players:
                if p.hero_id == 0: continue

                team = "Radiant" if p.player_slot < 128 else "Dire"

                all_results.append({
                    "match_id": m_id,
                    "date": readable_date,  # <--- НОВОЕ ПОЛЕ
                    "account_id": p.account_id,
                    "nickname": p.player_name if p.player_name else "Anonymous",
                    "hero": hero_map.get(str(p.hero_id), f"ID:{p.hero_id}"),
                    "team": team,
                    "win": "Yes" if team == winner_team else "No",
                    "kills": p.kills,
                    "deaths": p.deaths,
                    "assists": p.assists
                })
        else:
            print(f"⚠️ Матч {m_id} не ответил.")

        time.sleep(1.5)

    # Сохранение (Перезапись)
    if all_results:
        keys = all_results[0].keys()
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_results)
        print(f"🚀 Готово! Результаты в {OUTPUT_FILE}")

    dota.exit()
    client.disconnect()


# Используем твой рабочий метод входа
client.cli_login(username=STEAM_USERNAME, password=STEAM_PASSWORD)
client.run_forever()