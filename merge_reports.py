import csv
import os

DATA_DIR = 'data'
FINAL_REPORT = 'full_stats_report.csv'


def merge():
    all_data = []
    seen_records = set()
    # Словарь для хранения самого свежего ника: {account_id: {'nickname': name, 'date': date}}
    latest_nicknames = {}

    print("🔄 Начинаю сбор данных и актуализацию никнеймов...")

    # Шаг 1: Собираем все данные и находим последние ники
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

                    # 1. Проверка на дубликаты строк (как и было)
                    unique_key = f"{row['match_id']}_{acc_id}"
                    if unique_key not in seen_records:
                        all_data.append(row)
                        seen_records.add(unique_key)

                    # 2. Обновляем информацию о самом свежем нике для этого ID
                    if acc_id not in latest_nicknames or current_date > latest_nicknames[acc_id]['date']:
                        latest_nicknames[acc_id] = {
                            'nickname': current_nick,
                            'date': current_date
                        }

    if all_data:
        print("🛠 Применяю актуальные никнеймы ко всем записям...")
        # Шаг 2: Проходим по всем собранным данным и заменяем старые ники на новые
        for row in all_data:
            acc_id = row['account_id']
            row['nickname'] = latest_nicknames[acc_id]['nickname']

        # Шаг 3: Сохранение
        keys = all_data[0].keys()
        with open(FINAL_REPORT, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_data)

        print(f"🚀 Успех! Единый отчет создан: {FINAL_REPORT}")
        print(f"📊 Всего строк: {len(all_data)}")
        print(f"👤 Уникальных игроков: {len(latest_nicknames)}")
    else:
        print("📭 Нечего объединять.")


if __name__ == "__main__":
    merge()