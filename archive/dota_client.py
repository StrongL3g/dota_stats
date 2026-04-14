from gevent import monkey

monkey.patch_all()

import sys
from steam.client import SteamClient
from dota2.client import Dota2Client

# --- НАСТРОЙКИ ---
STEAM_USERNAME = 'STEAM_USERNAME'
STEAM_PASSWORD = 'STEAM_PASSWORD'
TEST_MATCH_ID = 8767848614  # Твой ID лобби

client = SteamClient()
dota = Dota2Client(client)


@client.on('logged_on')
def start_dota():
    print("Авторизация успешна. Входим в сеть Dota 2...")
    dota.launch()


@dota.on('ready')
def fetch_details():
    print(f"Запрашиваю детали матча {TEST_MATCH_ID}...")
    job_id = dota.request_match_details(TEST_MATCH_ID)
    res = dota.wait_msg(job_id, timeout=20)

    if res and hasattr(res, 'match'):
        match = res.match
        print("\n--- СТАТИСТИКА МАТЧА ПОЛУЧЕНА ---")

        # Пытаемся определить победителя через разные возможные поля
        match_outcome = "Неизвестно"
        if hasattr(match, 'radiant_win'):
            match_outcome = "Radiant" if match.radiant_win else "Dire"
        elif hasattr(match, 'outcome'):
            match_outcome = match.outcome  # Иногда бывает числом

        print(f"ID: {match.match_id}")
        print(f"Победитель: {match_outcome}")
        print(f"Длительность: {getattr(match, 'duration', '???')} сек.")

        print("\nСтатистика игроков:")
        print(f"{'ID Игрока':<12} | {'K':<3} | {'D':<3} | {'A':<3} | {'Герой ID'}")
        print("-" * 45)

        for p in getattr(match, 'players', []):
            p_id = getattr(p, 'account_id', '???')
            kills = getattr(p, 'kills', 0)
            deaths = getattr(p, 'deaths', 0)
            assists = getattr(p, 'assists', 0)
            h_id = getattr(p, 'hero_id', '???')
            print(f"{p_id:<12} | {kills:<3} | {deaths:<3} | {assists:<3} | {h_id}")

        # Магическая строка: выведет вообще все поля, которые есть в объекте игрока
        # Это поможет нам найти GPM, XPM и прочее для будущего приложения
        if len(match.players) > 0:
            print("\nДоступные поля игрока для анализа:")
            print(dir(match.players[0]))

    else:
        print("Не удалось получить структуру матча.")

    dota.exit()
    client.disconnect()

client.cli_login(username=STEAM_USERNAME, password=STEAM_PASSWORD)
client.run_forever()