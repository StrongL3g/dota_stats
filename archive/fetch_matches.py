import requests
import csv
import time

# --- НАСТРОЙКИ ---
API_KEY = 'API_KEY'  # Вставь сюда свой ключ
ACCOUNT_ID = 'ACCOUNT_ID'  # Твой SteamID32
FILE_NAME = 'dota_private_matches.csv'


def get_matches(account_id, start_at_match_id=None):
    """Получает список матчей игрока"""
    url = "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v1/"
    params = {
        'key': API_KEY,
        'account_id': account_id,
    }
    if start_at_match_id:
        params['start_at_match_id'] = start_at_match_id

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('result', {})
    else:
        print(f"Ошибка API: {response.status_code}")
        return None


def main():
    all_filtered_matches = []
    last_match_id = None
    print("Начинаю поиск матчей... Это может занять время.")

    while True:
        data = get_matches(ACCOUNT_ID, start_at_match_id=last_match_id)

        if not data or 'matches' not in data or len(data['matches']) == 0:
            break

        matches = data['matches']

        # --- ДИАГНОСТИЧЕСКИЙ БЛОК ---
        for m in matches[:15]:  # Смотрим только первые 5 для теста
            print(f"Матч ID: {m['match_id']} | LobbyType: {m.get('lobby_type')} | GameMode: {m.get('game_mode')}")

        # Оставим фильтрацию, но добавим вывод, если что-то нашлось
        for m in matches:
            # Давай временно расширим фильтр, чтобы поймать хоть что-то из лобби
            if m.get('lobby_type') in [0, 1, 7]:  # 0-паблик, 1-лобби, 7-ранкед
                all_filtered_matches.append({
                    'match_id': m['match_id'],
                    'start_time': m['start_time'],
                    'lobby_type': m['lobby_type'],
                    #'game_mode': m['game_mode']
                })
        # ----------------------------
        break  # Остановим после первой итерации для проверки

        # Запоминаем ID последнего матча, чтобы в следующей итерации начать С НЕГО
        new_last_id = matches[-1]['match_id']

        # Если мы получили меньше 100 матчей или ID не меняется - значит, дошли до конца
        if len(matches) < 100 or new_last_id == last_match_id:
            break

        last_match_id = new_last_id - 1  # Уменьшаем на 1, чтобы не дублировать последний матч
        print(f"Проверено до матча ID: {last_match_id}. Найдено нужных: {len(all_filtered_matches)}")

        # Небольшая пауза, чтобы Steam нас не заблокировал за частые запросы
        time.sleep(0.5)

    # Сохраняем результат в CSV
    if all_filtered_matches:
        keys = all_filtered_matches[0].keys()
        with open(FILE_NAME, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_filtered_matches)
        print(f"Готово! Сохранено {len(all_filtered_matches)} матчей в файл {FILE_NAME}")
    else:
        print("Подходящих матчей не найдено.")


if __name__ == "__main__":
    main()