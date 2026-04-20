import csv
import os

DATA_DIR = 'data'
FINAL_REPORT = 'full_stats_report.csv'


def merge():
    all_data = []
    seen_records = set()
    latest_nicknames = {}

    print("🔄 Начинаю сбор данных и актуализацию никнеймов...")

    for account_name in os.listdir(DATA_DIR):
        report_path = os.path.join(DATA_DIR, account_name, 'analytics_report.csv')

        if os.path.exists(report_path):
            print(f"  + Обработка отчета: {account_name}")
            with open(report_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    acc_id = row['account_id']
                    current_date = row['date']
                    current_nick = row['nickname']

                    # 1️⃣ Обновляем ники из ВСЕХ прочитанных матчей
                    # (чтобы не потерять свежие никнеймы, если последний матч был не Practice)
                    if acc_id not in latest_nicknames or current_date > latest_nicknames[acc_id]['date']:
                        latest_nicknames[acc_id] = {
                            'nickname': current_nick,
                            'date': current_date
                        }

                    # 2️⃣ Фильтрация: в итоговый отчет добавляем ТОЛЬКО lobby_type == 1
                    lobby_type = str(row.get('lobby_type', '')).strip()
                    # Поддерживаем и число '1', и название 'Practice' (зависит от того, как сохранил первый скрипт)
                    if lobby_type not in ('1', 'Practice'):
                        continue

                    # 3️⃣ Проверка на дубликаты
                    unique_key = f"{row['match_id']}_{acc_id}"
                    if unique_key not in seen_records:
                        all_data.append(row)
                        seen_records.add(unique_key)

    if all_data:
        print("🛠 Применяю актуальные никнеймы ко всем записям...")
        for row in all_data:
            acc_id = row['account_id']
            # Подставляем самый свежий ник, найденный на шаге 1
            row['nickname'] = latest_nicknames[acc_id]['nickname']

        keys = all_data[0].keys()
        with open(FINAL_REPORT, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_data)

        print(f"🚀 Успех! Единый отчет создан: {FINAL_REPORT}")
        print(f"📊 Всего строк (только Practice): {len(all_data)}")
        print(f"👤 Уникальных игроков: {len(latest_nicknames)}")
    else:
        print("📭 Нечего объединять (или в файлах нет матчей с lobby_type=1).")


if __name__ == "__main__":
    merge()