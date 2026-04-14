import requests
import datetime

# --- НАСТРОЙКИ ---
API_KEY = 'API_KEY'
ACCOUNT_ID = 'ACCOUNT_ID'  # Укажи здесь свой SteamID32
TARGET_MATCH_ID = 8767848614  # Тот самый ID для проверки


def fetch_recent_matches(count=100):
    url = "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v1/"
    params = {
        'key': API_KEY,
        'account_id': ACCOUNT_ID,
        'matches_requested': count
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json().get('result', {})
            matches = data.get('matches', [])

            print(f"{'Match ID':<15} | {'Lobby':<7} | {'Mode':<5} | {'Date'}")
            print("-" * 60)

            for m in matches:
                m_id = m.get('match_id', 0)
                # Используем str() и or '?', чтобы избежать ошибки NoneType
                l_type = str(m.get('lobby_type') if m.get('lobby_type') is not None else "?")
                g_mode = str(m.get('game_mode') if m.get('game_mode') is not None else "?")

                # Превращаем время
                start_time = m.get('start_time')
                date_str = datetime.datetime.fromtimestamp(start_time).strftime(
                    '%Y-%m-%d %H:%M') if start_time else "Unknown"

                # Пометка, если это наш искомый матч
                marker = ""
                if m_id == TARGET_MATCH_ID:
                    marker = " <--- ВОТ ОН!"
                elif l_type == "1":
                    marker = " <--- ЛОББИ"

                print(f"{str(m_id):<15} | {l_type:<7} | {g_mode:<5} | {date_str}{marker}")

            print("-" * 60)
            print(f"Всего найдено в истории: {len(matches)}")

        else:
            print(f"Ошибка API Steam: {response.status_code}")
    except Exception as e:
        print(f"Произошла ошибка в коде: {e}")


if __name__ == "__main__":
    fetch_recent_matches(50)  # Давай для начала глянем 50 матчей