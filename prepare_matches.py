import csv
import os

DATA_DIR = 'data'
ALLOWED_MODES = ['2', '16']


def prepare():
    if not os.path.exists(DATA_DIR):
        print(f"❌ Папка {DATA_DIR} не найдена")
        return

    # Перебираем папки аккаунтов
    for account_name in os.listdir(DATA_DIR):
        account_path = os.path.join(DATA_DIR, account_name)

        if os.path.isdir(account_path):
            input_file = os.path.join(account_path, 'dota_ids_for_api.csv')
            output_file = os.path.join(account_path, 'matches.csv')

            if os.path.exists(input_file):
                print(f"📦 Обработка аккаунта: {account_name}")
                unique_ids = set()

                with open(input_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('GameMode') in ALLOWED_MODES:
                            unique_ids.add(row.get('Match_ID'))

                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Match_ID'])
                    for m_id in sorted(list(unique_ids)):
                        writer.writerow([m_id])
                print(f"   ✅ Создан {output_file} ({len(unique_ids)} матчей)")


if __name__ == "__main__":
    prepare()