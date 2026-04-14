from gevent import monkey

monkey.patch_all()

import datetime
from steam.client import SteamClient
from dota2.client import Dota2Client

# --- НАСТРОЙКИ ---
STEAM_USERNAME = 'kajiu6'
STEAM_PASSWORD = '123Kowka123'
TEST_MATCH_ID = 8767848614

client = SteamClient()
dota = Dota2Client(client)


def inspect_object(obj, name):
    print(f"\n--- СПИСОК СВОЙСТВ ДЛЯ: {name} ---")
    # Descriptor.fields_by_name выводит только те поля, которые определены в протоколе Valve
    fields = sorted(obj.DESCRIPTOR.fields_by_name.keys())
    for field in fields:
        value = getattr(obj, field, "N/A")
        # Если значение слишком длинное (например, список), укоротим его для вывода
        str_val = str(value)
        if len(str_val) > 50: str_val = str_val[:47] + "..."
        print(f"{field:<30} : {str_val}")


@client.on('logged_on')
def start_dota():
    print("Авторизация успешна. Заходим в сеть...")
    dota.launch()


@dota.on('ready')
def fetch_and_inspect():
    print(f"Запрашиваю детали матча {TEST_MATCH_ID}...")
    job_id = dota.request_match_details(TEST_MATCH_ID)
    res = dota.wait_msg(job_id, timeout=20)

    if res and hasattr(res, 'match'):
        match = res.match

        # 1. Инспектируем сам МАТЧ
        inspect_object(match, "ОБЪЕКТ МАТЧА (MATCH)")

        # 2. Инспектируем ПЕРВОГО ИГРОКА в списке
        if len(match.players) > 0:
            inspect_object(match.players[0], "ОБЪЕКТ ИГРОКА (PLAYER_0)")
            inspect_object(match.players[1], "ОБЪЕКТ ИГРОКА (PLAYER_1)")
            inspect_object(match.players[2], "ОБЪЕКТ ИГРОКА (PLAYER_2)")
            inspect_object(match.players[3], "ОБЪЕКТ ИГРОКА (PLAYER_3)")
            inspect_object(match.players[4], "ОБЪЕКТ ИГРОКА (PLAYER_4)")
            inspect_object(match.players[5], "ОБЪЕКТ ИГРОКА (PLAYER_5)")
            inspect_object(match.players[6], "ОБЪЕКТ ИГРОКА (PLAYER_6)")
            inspect_object(match.players[7], "ОБЪЕКТ ИГРОКА (PLAYER_7)")
            inspect_object(match.players[8], "ОБЪЕКТ ИГРОКА (PLAYER_8)")
            inspect_object(match.players[9], "ОБЪЕКТ ИГРОКА (PLAYER_9)")

        print("\n" + "=" * 50)
        print("СОВЕТ: Ищи поля типа 'start_time', 'lobby_type', 'game_mode'.")
        print("Для времени используй datetime.fromtimestamp(match.start_time)")
    else:
        print("Не удалось получить данные.")

    dota.exit()
    client.disconnect()


client.cli_login(username=STEAM_USERNAME, password=STEAM_PASSWORD)
client.run_forever()