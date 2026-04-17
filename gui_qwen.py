import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
import pandas as pd


def get_resource_path(relative_path):
    """Получить абсолютный путь к ресурсу (работает в IDE и в .exe)"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class PlayerDetailWindow(tk.Toplevel):
    def __init__(self, parent, account_id, nickname, df, player_stats):
        super().__init__(parent)
        self.MIN_GAMES = 10
        self.TOP_HEROES = 10
        self.title(f"Детали игрока: {nickname} ({account_id})")
        self.geometry("900x700")
        self.account_id = int(account_id)
        self.nickname = nickname
        self.df = df
        self.player_stats = player_stats

        self.peer_stats = self._calculate_peer_stats()
        self.hero_stats = self._calculate_hero_stats()
        self._setup_ui()

    def _calculate_peer_stats(self):
        """Расчёт статистики по тиммейтам и врагам (≥5 совместных игр)"""
        player_matches = self.df[self.df['account_id'] == self.account_id]
        peer_data = {}

        for _, match in player_matches.iterrows():
            mid = match['match_id']
            team = match['team']
            player_won = match['win_binary']
            match_df = self.df[self.df['match_id'] == mid]

            # Тиммейты
            teammates = match_df[(match_df['team'] == team) & (match_df['account_id'] != self.account_id)]
            for _, p in teammates.iterrows():
                pid = int(p['account_id'])
                peer_data.setdefault(pid, {'nickname': p['nickname'], 'together_m': 0, 'together_w': 0, 'opposite_m': 0,
                                           'opposite_w': 0})
                peer_data[pid]['together_m'] += 1
                if player_won:
                    peer_data[pid]['together_w'] += 1

            # Враги
            opponents = match_df[match_df['team'] != team]
            for _, p in opponents.iterrows():
                pid = int(p['account_id'])
                peer_data.setdefault(pid, {'nickname': p['nickname'], 'together_m': 0, 'together_w': 0, 'opposite_m': 0,
                                           'opposite_w': 0})
                peer_data[pid]['opposite_m'] += 1
                if player_won:
                    peer_data[pid]['opposite_w'] += 1

        # Фильтр ≥5 игр
        valid = {k: v for k, v in peer_data.items() if v['together_m'] >= self.MIN_GAMES or v['opposite_m'] >= 5}
        for pid, d in valid.items():
            d['together_wr'] = (d['together_w'] / d['together_m'] * 100) if d['together_m'] >= self.MIN_GAMES else 0.0
            d['opposite_wr'] = (d['opposite_w'] / d['opposite_m'] * 100) if d['opposite_m'] >= self.MIN_GAMES else 0.0
            # 🔧 Теперь opposite_wr — это WINRATE ТЕКУЩЕГО игрока против этого врага

        together = [(k, v) for k, v in valid.items() if v['together_m'] >= self.MIN_GAMES]
        opposite = [(k, v) for k, v in valid.items() if v['opposite_m'] >= self.MIN_GAMES]

        # 🔍 DEBUG: вывод в консоль для проверки
        print(f"\n[DEBUG] {self.nickname} vs враги:")
        for pid, d in list(valid.items())[:3]:  # первые 3 врага
            if d['opposite_m'] >= 5:
                print(
                    f"  {d['nickname']}: {d['opposite_w']}/{d['opposite_m']} побед → {d['opposite_wr']:.1f}% (наш WR против них)")

        return {
            'best_tm': sorted(together, key=lambda x: x[1]['together_wr'], reverse=True)[:3],
            'worst_tm': sorted(together, key=lambda x: x[1]['together_wr'])[:3],
            'strongest_op': sorted(opposite, key=lambda x: x[1]['opposite_wr'], reverse=True)[:3],
            # 🔧 Сортируем по НАШЕМУ WR против них
            'weakest_op': sorted(opposite, key=lambda x: x[1]['opposite_wr'])[:3],
            'all': valid
        }

    def _calculate_hero_stats(self, min_games=3):
        """Расчёт статистики по героям (≥min_games игр)"""
        player_df = self.df[self.df['account_id'] == self.account_id]
        if player_df.empty:
            return {'best': [], 'worst': []}

        hero_agg = player_df.groupby('hero').agg(
            games=('match_id', 'count'),
            wins=('win_binary', 'sum')
        ).reset_index()

        hero_agg = hero_agg[hero_agg['games'] >= min_games].copy()
        hero_agg['win_rate'] = (hero_agg['wins'] / hero_agg['games'] * 100).round(1)

        best = hero_agg.nlargest(self.TOP_HEROES, 'win_rate')[['hero', 'games', 'win_rate']].values.tolist()
        worst = hero_agg.nsmallest(self.TOP_HEROES, 'win_rate')[['hero', 'games', 'win_rate']].values.tolist()

        return {'best': best, 'worst': worst}

    def _setup_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tab_peers = ttk.Frame(nb)
        tab_heroes = ttk.Frame(nb)
        tab_compare = ttk.Frame(nb)

        nb.add(tab_peers, text="👥 Тиммейты и Враги")
        nb.add(tab_heroes, text="🦸 Герои")
        nb.add(tab_compare, text="⚖️ Сравнение")

        self._build_peers_tab(tab_peers)
        self._build_heroes_tab(tab_heroes)
        self._build_compare_tab(tab_compare)

    def _build_peers_tab(self, frame):
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        lists = [
            ("🟢 Лучшие тиммейты", 'best_tm', True),
            ("🔴 Худшие тиммейты", 'worst_tm', True),
            ("💪 Слабейшие враги (наш WR против них)", 'strongest_op', False),
            ("🥬 Сильнейшие враги (наш WR против них)", 'weakest_op', False)
        ]

        for idx, (title, key, is_team) in enumerate(lists):
            f = ttk.LabelFrame(frame, text=title)
            f.grid(row=idx // 2, column=idx % 2, padx=5, pady=5, sticky="nsew")  # 🔧 col → column

            tree = ttk.Treeview(f, columns=("nick", "games", "wr"), show="headings", height=4)
            tree.heading("nick", text="Никнейм")
            tree.heading("games", text="Игр")
            tree.heading("wr", text="Наш WR %")  # 🔧 Уточнённый заголовок
            tree.column("nick", width=180)
            tree.column("games", width=50, anchor=tk.CENTER)
            tree.column("wr", width=70, anchor=tk.CENTER)

            data_list = self.peer_stats[key]
            for pid, d in data_list:
                # 🔧 Для врагов показываем opposite_wr (наш винрейт против них)
                wr = d['together_wr'] if is_team else d['opposite_wr']
                games = d['together_m'] if is_team else d['opposite_m']
                tree.insert("", tk.END, values=(d['nickname'], games, f"{wr:.1f}%"))

            tree.pack(fill=tk.BOTH, expand=True)

    def _build_heroes_tab(self, frame):
        """Вкладка со статистикой по героям"""
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        # Лучшие герои
        best_frame = ttk.LabelFrame(frame, text="🏆 Лучшие герои (по винрейту)")
        best_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        best_tree = ttk.Treeview(best_frame, columns=("hero", "games", "wr"), show="headings", height=4)
        best_tree.heading("hero", text="Герой")
        best_tree.heading("games", text="Игр")
        best_tree.heading("wr", text="WR %")
        best_tree.column("hero", width=160)
        best_tree.column("games", width=50, anchor=tk.CENTER)
        best_tree.column("wr", width=60, anchor=tk.CENTER)

        for hero, games, wr in self.hero_stats['best']:
            best_tree.insert("", tk.END, values=(hero, games, f"{wr:.1f}%"))
        best_tree.pack(fill=tk.BOTH, expand=True)

        # Худшие герои
        worst_frame = ttk.LabelFrame(frame, text="📉 Худшие герои (по винрейту)")
        worst_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        worst_tree = ttk.Treeview(worst_frame, columns=("hero", "games", "wr"), show="headings", height=4)
        worst_tree.heading("hero", text="Герой")
        worst_tree.heading("games", text="Игр")
        worst_tree.heading("wr", text="WR %")
        worst_tree.column("hero", width=160)
        worst_tree.column("games", width=50, anchor=tk.CENTER)
        worst_tree.column("wr", width=60, anchor=tk.CENTER)

        for hero, games, wr in self.hero_stats['worst']:
            worst_tree.insert("", tk.END, values=(hero, games, f"{wr:.1f}%"))
        worst_tree.pack(fill=tk.BOTH, expand=True)

        # 🔧 Подсказка, если данных мало
        if not self.hero_stats['best'] and not self.hero_stats['worst']:
            info = ttk.Label(frame, text=f"⚠️ Нет героев с ≥3 играми для статистики", foreground="gray")
            info.grid(row=1, column=0, columnspan=2, pady=10)

    def _build_compare_tab(self, frame):
        ttk.Label(frame, text="Выберите второго игрока для сравнения:").pack(anchor=tk.W, padx=10, pady=(10, 0))

        players = sorted([(r['account_id'], r['nickname']) for _, r in self.player_stats.iterrows()
                          if r['account_id'] != self.account_id], key=lambda x: x[1])

        self.compare_var = StringVar()
        cb = ttk.Combobox(frame, textvariable=self.compare_var,
                          values=[f"{nid} | {nname}" for nid, nname in players], state="readonly", width=50)
        cb.pack(padx=10, pady=5)
        if players:
            cb.current(0)

        ttk.Button(frame, text="🔍 Сравнить", command=self._run_comparison).pack(pady=5)

        self.compare_text = tk.Text(frame, height=12, state=tk.DISABLED, wrap=tk.WORD, font=("Consolas", 10))
        self.compare_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _run_comparison(self):
        sel = self.compare_var.get()
        if not sel: return
        target_id = int(sel.split(" | ")[0])

        common_mids = set(self.df[self.df['account_id'] == self.account_id]['match_id']) & \
                      set(self.df[self.df['account_id'] == target_id]['match_id'])

        tog_m = tog_w = opp_m = opp_w = 0
        for mid in common_mids:
            p = self.df[(self.df['match_id'] == mid) & (self.df['account_id'] == self.account_id)].iloc[0]
            t = self.df[(self.df['match_id'] == mid) & (self.df['account_id'] == target_id)].iloc[0]
            if p['team'] == t['team']:
                tog_m += 1
                if p['win_binary']: tog_w += 1
            else:
                opp_m += 1
                if p['win_binary']: opp_w += 1

        nick = self.peer_stats['all'].get(target_id, {}).get('nickname', str(target_id))
        res = f"📊 Сравнение: {self.nickname} vs {nick} ({target_id})\n"
        res += "=" * 55 + "\n"
        res += f"🤝 Вместе: {tog_m} матчей | Ваш WR: {(tog_w / tog_m * 100 if tog_m else 0):.1f}%\n"
        res += f"⚔️ Против: {opp_m} матчей | Ваш WR: {(opp_w / opp_m * 100 if opp_m else 0):.1f}%\n"

        if tog_m >= 5 or opp_m >= 5:
            res += "\n✅ Попадает в топ-списки (≥5 игр)"
        else:
            res += f"\n⚠️ Сыграно менее 5 игр. Не попадает в топ-списки."

        self.compare_text.config(state=tk.NORMAL)
        self.compare_text.delete("1.0", tk.END)
        self.compare_text.insert(tk.END, res)
        self.compare_text.config(state=tk.DISABLED)


class DotaStatsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 Dota 2 Hidden Lobby Stats")
        self.root.geometry("1100x900")
        self.root.minsize(950, 700)

        self.csv_path = get_resource_path("full_stats_report.csv")
        self.df = None
        self.player_stats = None
        self.sort_order = {}

        self._load_data()
        if self.df is None:
            messagebox.showerror("Ошибка", "Файл 'full_stats_report.csv' не найден или имеет неверный формат.")
            self.root.destroy()
            return

        self._setup_main_ui()

    def _load_data(self):
        try:
            self.df = pd.read_csv(self.csv_path)
            # 🔧 Приводим типы данных для надёжности
            self.df['match_id'] = self.df['match_id'].astype(int)
            self.df['account_id'] = self.df['account_id'].astype(int)
            self.df['win_binary'] = (self.df['win'].str.strip().str.lower() == 'yes').astype(int)
            # KDA: (K+A)/D, если D=0 → K+A
            self.df['kda_row'] = self.df.apply(
                lambda r: (r['kills'] + r['assists']) / r['deaths'] if r['deaths'] > 0 else r['kills'] + r['assists'],
                axis=1
            )

            # Агрегация по игрокам
            agg = self.df.groupby(['account_id', 'nickname']).agg(
                matches=('match_id', 'count'),
                wins=('win_binary', 'sum'),
                kills=('kills', 'sum'),
                deaths=('deaths', 'sum'),
                assists=('assists', 'sum')
            ).reset_index()

            agg['win_rate'] = (agg['wins'] / agg['matches'] * 100).round(2)
            agg['avg_kda'] = agg.apply(
                lambda r: (r['kills'] + r['assists']) / r['deaths'] if r['deaths'] > 0 else r['kills'] + r['assists'],
                axis=1
            ).round(2)
            self.player_stats = agg
        except FileNotFoundError:
            messagebox.showerror("Файл не найден", f"Не удалось найти:\n{self.csv_path}")
            self.df = None
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", f"{type(e).__name__}: {e}")
            self.df = None

    def _setup_main_ui(self):
        # 🔍 Поиск
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(search_frame, text="🔍 Поиск по нику/ID:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_players())
        ttk.Entry(search_frame, textvariable=self.search_var, width=35).pack(side=tk.LEFT)
        ttk.Button(search_frame, text="👤 Детали", command=self._open_detail_selected).pack(side=tk.RIGHT, padx=5)

        # 📋 Главная таблица игроков
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.player_tree = ttk.Treeview(
            top_frame,
            columns=("account_id", "nickname", "matches", "win_rate", "avg_kda"),
            show="headings"
        )
        headers = [
            ("account_id", "ID", 80),
            ("nickname", "Никнейм", 180),
            ("matches", "Матчи", 70),
            ("win_rate", "WR %", 75),
            ("avg_kda", "KDA", 80)
        ]
        for col, text, width in headers:
            self.player_tree.heading(col, text=text, command=lambda c=col: self._sort_treeview(c))
            self.player_tree.column(col, width=width, anchor=tk.CENTER)

        self.player_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(top_frame, orient=tk.VERTICAL, command=self.player_tree.yview)
        self.player_tree.configure(yscroll=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.player_tree.bind("<<TreeviewSelect>>", self._on_player_select)
        self.player_tree.bind("<Double-1>", lambda e: self._open_detail_selected())
        self._populate_player_tree()

        # 🎮 История матчей
        mid_frame = ttk.LabelFrame(self.root, text="📜 История матчей выбранного игрока")
        mid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        match_cols = ("match_id", "date", "hero", "team", "win", "kills", "deaths", "assists", "kda")
        self.match_tree = ttk.Treeview(mid_frame, columns=match_cols, show="headings", height=7)
        for c in match_cols:
            self.match_tree.heading(c, text=c.upper().replace('_', ' '))
            self.match_tree.column(c, width=75, anchor=tk.CENTER)
        self.match_tree.column("hero", width=120)
        self.match_tree.column("date", width=140)

        self.match_tree.pack(fill=tk.BOTH, expand=True)
        self.match_tree.bind("<<TreeviewSelect>>", lambda e: self._show_match_details())

        # 📄 Детали матча
        bot_frame = ttk.LabelFrame(self.root, text="🔍 Детали матча")
        bot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.details_text = tk.Text(bot_frame, height=5, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 9))
        self.details_text.pack(fill=tk.BOTH, expand=True)

    def _populate_player_tree(self):
        for i in self.player_tree.get_children():
            self.player_tree.delete(i)

        df = self.player_stats.copy()
        query = self.search_var.get().strip().lower()
        if query:
            df = df[
                df['nickname'].str.lower().str.contains(query) |
                df['account_id'].astype(str).str.contains(query)
                ]

        sort_col = self.sort_order.get('col', 'matches')
        asc = self.sort_order.get('asc', False)
        df = df.sort_values(sort_col, ascending=asc)

        for _, row in df.iterrows():
            self.player_tree.insert("", tk.END, values=(
                row["account_id"], row["nickname"], row["matches"],
                f"{row['win_rate']:.1f}", f"{row['avg_kda']:.2f}"
            ))

    def _filter_players(self):
        self._populate_player_tree()

    def _sort_treeview(self, col):
        current_asc = self.sort_order.get('col') == col and not self.sort_order.get('asc', True)
        self.sort_order = {'col': col, 'asc': current_asc}
        self._populate_player_tree()

    def _on_player_select(self, event):
        sel = self.player_tree.selection()
        if not sel: return
        acc_id = int(self.player_tree.item(sel[0], "values")[0])
        self._populate_match_history(acc_id)

    def _populate_match_history(self, account_id):
        for i in self.match_tree.get_children():
            self.match_tree.delete(i)

        pm = self.df[self.df['account_id'] == account_id].sort_values('date', ascending=False)
        for _, r in pm.iterrows():
            self.match_tree.insert("", tk.END, values=(
                r['match_id'], r['date'], r['hero'], r['team'], r['win'],
                r['kills'], r['deaths'], r['assists'], f"{r['kda_row']:.2f}"
            ))

        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, "💡 Выберите матч в списке или сделайте двойной клик для просмотра деталей")
        self.details_text.config(state=tk.DISABLED)

    def _show_match_details(self):
        sel = self.match_tree.selection()
        if not sel: return

        match_id = int(self.match_tree.item(sel[0], "values")[0])
        mdf = self.df[self.df['match_id'] == match_id]

        if mdf.empty:
            self._show_detail_text(f"⚠️ Не удалось загрузить детали матча {match_id}")
            return

        res = f"🎮 Матч #{match_id} | 📅 {mdf.iloc[0]['date']}\n" + "=" * 60 + "\n"
        for side in ['Radiant', 'Dire']:
            sdf = mdf[mdf['team'] == side]
            if sdf.empty: continue
            result = "🏆 ПОБЕДА" if sdf.iloc[0]['win_binary'] else "💀 Поражение"
            side_icon = "🟢" if side == 'Radiant' else "🔴"
            res += f"{side_icon} {side}: {result}\n" + "-" * 40 + "\n"
            for _, p in sdf.iterrows():
                kda = f"{p['kda_row']:.2f}"
                res += f"  {p['nickname']:<20} {p['hero']:<14} K:{p['kills']:2} D:{p['deaths']:2} A:{p['assists']:2} | KDA:{kda}\n"
            res += "\n"

        self._show_detail_text(res)

    def _show_detail_text(self, text):
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, text)
        self.details_text.config(state=tk.DISABLED)

    def _open_detail_selected(self):
        sel = self.player_tree.selection()
        if not sel:
            messagebox.showinfo("Подсказка", "👆 Сначала выберите игрока в таблице выше")
            return
        acc_id = self.player_tree.item(sel[0], "values")[0]
        nick = self.player_tree.item(sel[0], "values")[1]
        PlayerDetailWindow(self.root, acc_id, nick, self.df, self.player_stats)


if __name__ == "__main__":
    try:
        import pandas as pd
    except ImportError:
        print("❌ Требуется pandas. Установите: pip install pandas")
        sys.exit(1)

    root = tk.Tk()
    # 🔧 Тема для лучшего вида на разных ОС
    style = ttk.Style()
    if "win" in sys.platform:
        style.theme_use('vista')
    elif "darwin" in sys.platform:
        style.theme_use('aqua')
    else:
        style.theme_use('clam')

    app = DotaStatsGUI(root)
    root.mainloop()