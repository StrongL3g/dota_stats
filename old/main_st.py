#
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QLabel, QComboBox, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt

import os
import sys

# Определяем путь к папке, где лежит сам EXE или скрипт
if getattr(sys, 'frozen', False):
    # Если запущено как EXE
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Если запущено как обычный .py
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Теперь используем BASE_DIR для всех путей
FILE_PATH = os.path.join(BASE_DIR, "dota_stats_StrongLeg.csv")
FRIENDS_PATH = os.path.join(BASE_DIR, "friends.json")
HEROES_PATH = os.path.join(BASE_DIR, "heroes.json")

class DotaStatsApp(QMainWindow):
    def __init__(self, file_path):
        super().__init__()
        self.setWindowTitle("Dota 2 Team Analytics")
        self.resize(1200, 800)

        # Загрузка данных
        try:
            self.df = pd.read_csv(file_path)
            # Приводим типы данных для корректных расчетов
            self.df['Is_Winner'] = self.df['Is_Winner'].map({'Yes': True, 'No': False})
        except Exception as e:
            print(f"Ошибка загрузки файла: {e}")
            sys.exit()

        self.current_player = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- ТАБЛИЦА СТИЛЕЙ (QSS) ---
        # Это заставит приложение выглядеть корректно и в светлой, и в темной теме Windows
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; }
            QLabel { color: #ffffff; }
            QTableWidget { 
                background-color: #3c3f41; 
                color: #ffffff; 
                gridline-color: #555555;
                selection-background-color: #4b6eaf;
            }
            QHeaderView::section {
                background-color: #3c3f41;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #555555;
            }
            QComboBox { 
                background-color: #3c3f41; 
                color: #ffffff; 
                border: 1px solid #555555;
            }
        """)

        # --- ВЕРХНЯЯ ПАНЕЛЬ ---
        top_label = QLabel("📊 Общая статистика всех игроков")
        top_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        main_layout.addWidget(top_label)

        self.main_table = QTableWidget()
        self.main_table.setColumnCount(5)
        self.main_table.setHorizontalHeaderLabels(["Никнейм", "Матчей", "Винрейт %", "Средний KDA", "Account_ID"])
        self.main_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.main_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.main_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.main_table.setSortingEnabled(True)
        self.main_table.cellClicked.connect(self.load_player_details)
        main_layout.addWidget(self.main_table, 2)

        # --- СРЕДНЯЯ ПАНЕЛЬ ---
        filter_layout = QHBoxLayout()
        self.player_label = QLabel("Выбранный игрок: Выберите в таблице")
        self.player_label.setStyleSheet("font-weight: bold; color: #76a9ff;")

        self.compare_box = QComboBox()
        self.compare_box.addItem("Сравнить с...")
        self.compare_box.currentIndexChanged.connect(self.update_comparison)

        self.side_filter = QComboBox()
        self.side_filter.addItems(["В одной команде (ЗА)", "В разных командах (ПРОТИВ)"])
        self.side_filter.currentIndexChanged.connect(self.update_comparison)

        filter_layout.addWidget(self.player_label)
        filter_layout.addStretch()
        filter_layout.addWidget(QLabel("Сравнить с:"))
        filter_layout.addWidget(self.compare_box)
        filter_layout.addWidget(self.side_filter)
        main_layout.addLayout(filter_layout)

        # --- НИЖНЯЯ ПАНЕЛЬ (Блок анализа) ---
        self.detail_info = QLabel("Здесь будет статистика связки")
        # Теперь используем темный фон и светлый текст
        self.detail_info.setStyleSheet("""
            background-color: #1e1e1e; 
            color: #00ff00; 
            padding: 10px; 
            border: 1px solid #333333;
            border-radius: 5px;
            font-family: 'Consolas', monospace;
        """)
        main_layout.addWidget(self.detail_info)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ["ID Матча", "Команда", "Победа?", "Герой", "K/D/A", "Длительность"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.history_table, 3)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.populate_main_table()
        self.populate_compare_list()

    def populate_main_table(self):
        # Группируем данные по Nickname
        stats = self.df.groupby('Nickname').agg({
            'Match_ID': 'count',
            'Is_Winner': 'mean',
            'K': 'mean',
            'D': 'mean',
            'A': 'mean',
            'Account_ID': 'first'
        }).reset_index()

        self.main_table.setRowCount(len(stats))
        for i, row in stats.iterrows():
            wr = row['Is_Winner'] * 100
            kda = (row['K'] + row['A']) / max(row['D'], 1)

            # Используем setData для корректной сортировки чисел
            item_name = QTableWidgetItem(str(row['Nickname']))

            item_matches = QTableWidgetItem()
            item_matches.setData(Qt.ItemDataRole.DisplayRole, int(row['Match_ID']))

            item_wr = QTableWidgetItem()
            item_wr.setData(Qt.ItemDataRole.DisplayRole, f"{wr:.1f}%")

            item_kda = QTableWidgetItem()
            item_kda.setData(Qt.ItemDataRole.DisplayRole, f"{kda:.2f}")

            item_id = QTableWidgetItem(str(row['Account_ID']))

            self.main_table.setItem(i, 0, item_name)
            self.main_table.setItem(i, 1, item_matches)
            self.main_table.setItem(i, 2, item_wr)
            self.main_table.setItem(i, 3, item_kda)
            self.main_table.setItem(i, 4, item_id)

    def populate_compare_list(self):
        self.compare_box.clear()
        self.compare_box.addItem("Сравнить с...")
        players = sorted(self.df['Nickname'].unique().tolist())
        self.compare_box.addItems(players)

    def load_player_details(self, row, column):
        self.current_player = self.main_table.item(row, 0).text()
        self.player_label.setText(f"Выбранный игрок: {self.current_player}")
        self.update_history_table(self.df[self.df['Nickname'] == self.current_player])
        self.update_comparison()

    def update_history_table(self, data):
        self.history_table.setRowCount(len(data))
        for i, (_, row) in enumerate(data.iterrows()):
            res = "🏆 Победа" if row['Is_Winner'] else "❌ Поражение"
            kda_str = f"{row['K']}/{row['D']}/{row['A']}"

            self.history_table.setItem(i, 0, QTableWidgetItem(str(row['Match_ID'])))
            self.history_table.setItem(i, 1, QTableWidgetItem(row['Team']))
            self.history_table.setItem(i, 2, QTableWidgetItem(res))
            self.history_table.setItem(i, 3, QTableWidgetItem(row['Hero_Name']))
            self.history_table.setItem(i, 4, QTableWidgetItem(kda_str))
            self.history_table.setItem(i, 5, QTableWidgetItem(row['Duration']))

    def update_comparison(self):
        target = self.compare_box.currentText()
        if not self.current_player or target == "Сравнить с...":
            return

        # Находим все ID матчей основного игрока
        p1_matches = self.df[self.df['Nickname'] == self.current_player]

        # Находим все записи второго игрока
        p2_data = self.df[self.df['Nickname'] == target]

        # Объединяем, чтобы найти общие матчи
        common_matches = pd.merge(p1_matches, p2_data, on='Match_ID', suffixes=('_p1', '_p2'))

        if self.side_filter.currentIndex() == 0:  # ЗА (в одной команде)
            linked = common_matches[common_matches['Team_p1'] == common_matches['Team_p2']]
            mode_text = "в одной команде"
        else:  # ПРОТИВ
            linked = common_matches[common_matches['Team_p1'] != common_matches['Team_p2']]
            mode_text = "друг против друга"

        matches_count = len(linked)
        if matches_count > 0:
            winrate = linked['Is_Winner_p1'].mean() * 100
            self.detail_info.setText(
                f"📊 Анализ: {self.current_player} vs {target} ({mode_text})\n"
                f"Общих игр: {matches_count} | Винрейт: {winrate:.1f}%"
            )
            # Обновляем таблицу истории только этими матчами
            match_ids = linked['Match_ID'].unique()
            self.update_history_table(p1_matches[p1_matches['Match_ID'].isin(match_ids)])
        else:
            self.detail_info.setText(f"Общих игр {mode_text} не найдено.")
            self.history_table.setRowCount(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Укажи здесь имя своего файла
    window = DotaStatsApp("dota_stats_StrongLeg.csv")
    window.show()
    sys.exit(app.exec())