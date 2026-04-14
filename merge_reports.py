import csv
import os

DATA_DIR = 'data'
FINAL_REPORT = 'full_stats_report.csv'


def merge():
    all_data = []
    seen_records = set()  # Для удаления дубликатов (match_id + account_id)

    print("🔄 Начинаю объединение отчетов...")

    for account_name in os.listdir(DATA_DIR):
        report_path = os.path.join(DATA_DIR, account_name, 'analytics_report.csv')

        if os.path.exists(report_path):
            print(f"  + Добавляю отчет от {account_name}")
            with open(report_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Создаем уникальный ключ: ID матча + ID игрока
                    # Чтобы если один и тот же матч есть у двух друзей, он не дублировался
                    unique_key = f"{row['match_id']}_{row['account_id']}"

                    if unique_key not in seen_records:
                        all_data.append(row)
                        seen_records.add(unique_key)

    if all_data:
        keys = all_data[0].keys()
        with open(FINAL_REPORT, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_data)
        print(f"🚀 Успех! Единый отчет создан: {FINAL_REPORT}")
        print(f"📊 Всего строк статистики: {len(all_data)}")
    else:
        print("📭 Нечего объединять. Убедись, что analytics_report.csv созданы.")


if __name__ == "__main__":
    merge()