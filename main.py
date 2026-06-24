from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.utils import platform
import json
import os
from random import randint

# ======================== 配置 ========================
GRID_SIZE = 5
RECORD_FILE = "lights_out_record.json"

# 安卓平台使用 app 私有存储目录
if platform == 'android':
    try:
        from android.storage import app_storage_path
        RECORD_FILE = os.path.join(app_storage_path(), "lights_out_record.json")
    except ImportError:
        RECORD_FILE = "lights_out_record.json"

# ======================== 游戏状态 ========================
class GameState:
    def __init__(self):
        self.light_states = []       # 灯的状态矩阵
        self.current_steps = 0       # 当前步数
        self.start_time = None       # 开始时间
        self.timer_event = None      # 计时器事件
        self.best_record = {}        # 最佳记录 {grid_size: (steps, time)}
        self.load_record()

    def load_record(self):
        default_record = {i: (float("inf"), float("inf")) for i in range(2, 11)}
        try:
            if os.path.exists(RECORD_FILE):
                with open(RECORD_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.best_record = {int(k): (float(v[0]), float(v[1])) for k, v in loaded.items()}
                for i in range(2, 11):
                    if i not in self.best_record:
                        self.best_record[i] = default_record[i]
            else:
                self.best_record = default_record
        except Exception:
            self.best_record = default_record

    def save_record(self):
        try:
            save_data = {str(k): list(v) for k, v in self.best_record.items()}
            with open(RECORD_FILE, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def reset_game(self):
        """生成一局新游戏"""
        self.current_steps = 0
        self.start_time = None
        if self.timer_event:
            Clock.unschedule(self.timer_event)
            self.timer_event = None
        # 随机点击若干次制造谜题
        self.light_states = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        rand_clicks = 25
        for _ in range(rand_clicks):
            r = randint(0, GRID_SIZE - 1)
            c = randint(0, GRID_SIZE - 1)
            self._toggle(r, c)

    def _toggle(self, r, c):
        """切换 (r,c) 及其上下左右的状态"""
        dirs = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                self.light_states[nr][nc] = not self.light_states[nr][nc]

    def click(self, r, c):
        """玩家点击 (r,c)"""
        if self.start_time is None:
            self.start_time = Clock.get_time()
            self.timer_event = Clock.schedule_interval(lambda dt: None, 0.01)  # 保持计时器活跃
        self._toggle(r, c)
        self.current_steps += 1

    def get_elapsed(self):
        if self.start_time is None:
            return 0.0
        return Clock.get_time() - self.start_time

    def check_win(self):
        return all(not cell for row in self.light_states for cell in row)


# ======================== 灯光按钮 ========================
class LightButton(Button):
    def __init__(self, row, col, game_state, **kwargs):
        super().__init__(**kwargs)
        self.row = row
        self.col = col
        self.game_state = game_state
        self.background_normal = ''
        self.background_color = (0.27, 0.27, 0.27, 1)
        self.bind(on_press=self.on_click)

    def on_click(self, instance):
        self.game_state.click(self.row, self.col)
        self.parent.refresh_buttons()
        self._update_win_check()

    def _update_win_check(self):
        if self.game_state.check_win():
            if self.game_state.timer_event:
                Clock.unschedule(self.game_state.timer_event)
                self.game_state.timer_event = None
            use_time = self.game_state.get_elapsed()
            best_step, best_t = self.game_state.best_record.get(GRID_SIZE, (float("inf"), float("inf")))
            app = App.get_running_app()
            if self.game_state.current_steps < best_step or \
               (self.game_state.current_steps == best_step and use_time < best_t):
                self.game_state.best_record[GRID_SIZE] = (self.game_state.current_steps, use_time)
                self.game_state.save_record()
            # 更新最佳记录显示
            root = app.root
            if root:
                root.update_best_label(GRID_SIZE, self.game_state.best_record)
            # 弹窗
            from kivy.uix.label import Label as KvLabel
            content = BoxLayout(orientation='vertical', padding=20, spacing=10)
            content.add_widget(KvLabel(
                text=f'步数: {self.game_state.current_steps}\n用时: {root.format_time(use_time)}',
                halign='center'
            ))
            btn = Button(text='再来一局', size_hint=(1, 0.4))
            popup = Popup(title='🎉 游戏胜利', content=content, size_hint=(0.8, 0.45))
            btn.bind(on_press=lambda x: (popup.dismiss(), root.reset_game()))
            content.add_widget(btn)
            popup.open()

    def update_visual(self):
        is_on = self.game_state.light_states[self.row][self.col]
        self.background_color = (0.98, 0.82, 0.14, 1) if is_on else (0.27, 0.27, 0.27, 1)


# ======================== 游戏网格 ========================
class LightGrid(GridLayout):
    def __init__(self, game_state, **kwargs):
        super().__init__(**kwargs)
        self.cols = GRID_SIZE
        self.rows = GRID_SIZE
        self.game_state = game_state
        self.buttons = []
        self._init_buttons()

    def _init_buttons(self):
        self.clear_widgets()
        self.buttons = []
        for r in range(GRID_SIZE):
            row_btns = []
            for c in range(GRID_SIZE):
                btn = LightButton(r, c, self.game_state)
                self.add_widget(btn)
                row_btns.append(btn)
            self.buttons.append(row_btns)
        self.refresh_buttons()

    def refresh_buttons(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.buttons[r][c].update_visual()


# ======================== 根布局 ========================
class GameRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [20, 20, 20, 20]
        self.spacing = 10
        self.game_state = GameState()

        # 顶部信息栏
        info_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        self.step_label = Label(text="步数: 0", size_hint=(0.3, 1))
        self.time_label = Label(text="用时: 00:00.000", size_hint=(0.4, 1))
        self.best_label = Label(text="最佳: 暂无", size_hint=(0.3, 1))
        info_layout.add_widget(self.step_label)
        info_layout.add_widget(self.time_label)
        info_layout.add_widget(self.best_label)
        self.add_widget(info_layout)

        # 游戏网格
        self.grid = LightGrid(self.game_state, size_hint=(1, 0.8))
        self.add_widget(self.grid)

        # 底部按钮
        btn_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        reset_btn = Button(text="重新开始")
        reset_btn.bind(on_press=lambda x: self.reset_game())
        btn_layout.add_widget(reset_btn)
        self.add_widget(btn_layout)

        # 初始化显示
        self.reset_game()
        self.update_best_label(GRID_SIZE, self.game_state.best_record)

        # 启动计时器刷新
        Clock.schedule_interval(self._timer_tick, 0.05)

    def _timer_tick(self, dt):
        if self.game_state.start_time is not None:
            elapsed = self.game_state.get_elapsed()
            self.time_label.text = f"用时: {self.format_time(elapsed)}"
        self.step_label.text = f"步数: {self.game_state.current_steps}"

    def reset_game(self):
        self.game_state.reset_game()
        self.grid.refresh_buttons()
        self.step_label.text = "步数: 0"
        self.time_label.text = "用时: 00:00.000"

    def update_best_label(self, grid_size, best_record):
        best_step, best_t = best_record.get(grid_size, (float("inf"), float("inf")))
        if best_step != float("inf"):
            self.best_label.text = f"最佳: {int(best_step)}步/{self.format_time(best_t)}"
        else:
            self.best_label.text = "最佳: 暂无"

    @staticmethod
    def format_time(sec):
        m = int(sec // 60)
        s = int(sec % 60)
        ms = int((sec - int(sec)) * 1000)
        return f"{m:02d}:{s:02d}.{ms:03d}"


# ======================== App 类 ========================
class GameApp(App):
    def build(self):
        return GameRoot()


if __name__ == "__main__":
    GameApp().run()
