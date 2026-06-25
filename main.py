import json
import os
import sys
import time
from random import randint

# ======================== Kivy 配置（必须在 kivy 之前）========================
from kivy.config import Config
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.utils import platform
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.widget import Widget

# ======================== 配置 ========================
GRID_SIZE = 5
RECORD_FILE = "lights_out_record.json"

if platform == 'android':
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        RECORD_FILE = os.path.join(
            PythonActivity.mActivity.getFilesDir().getAbsolutePath(),
            "lights_out_record.json"
        )
    except Exception:
        RECORD_FILE = "lights_out_record.json"


def log_error(msg):
    """将错误信息写入文件"""
    try:
        log_path = RECORD_FILE.replace(".json", "_crash_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("%s\n" % msg)
    except Exception:
        pass


class GameState:
    def __init__(self):
        self.light_states = []
        self.current_steps = 0
        self.start_time = None
        self.timer_event = None
        self.best_record = {}
        self.load_record()

    def load_record(self):
        default_record = {i: (float("inf"), float("inf")) for i in range(2, 11)}
        try:
            if os.path.exists(RECORD_FILE):
                with open(RECORD_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.best_record = {
                        int(k): (float(v[0]), float(v[1]))
                        for k, v in loaded.items()
                    }
                for i in range(2, 11):
                    if i not in self.best_record:
                        self.best_record[i] = default_record[i]
            else:
                self.best_record = default_record
        except Exception as e:
            log_error("GameState.load_record error: %s" % str(e))
            self.best_record = default_record

    def save_record(self):
        try:
            save_data = {str(k): list(v) for k, v in self.best_record.items()}
            with open(RECORD_FILE, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_error("GameState.save_record error: %s" % str(e))

    def reset_game(self):
        self.current_steps = 0
        self.start_time = None
        if self.timer_event:
            Clock.unschedule(self.timer_event)
            self.timer_event = None
        self.light_states = [
            [False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)
        ]
        rand_clicks = 25
        for _ in range(rand_clicks):
            r = randint(0, GRID_SIZE - 1)
            c = randint(0, GRID_SIZE - 1)
            self._toggle(r, c)

    def _toggle(self, r, c):
        dirs = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                self.light_states[nr][nc] = not self.light_states[nr][nc]

    def click(self, r, c):
        if self.start_time is None:
            self.start_time = time.time()
            self.timer_event = Clock.schedule_interval(lambda dt: None, 0.01)
        self._toggle(r, c)
        self.current_steps += 1

    def get_elapsed(self):
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def check_win(self):
        return all(not cell for row in self.light_states for cell in row)


class LightButton(Widget):
    """自定义灯按钮：用 Canvas 绘制，避免原生 Button 的兼容性问题"""

    def __init__(self, row, col, game_state, **kwargs):
        super(LightButton, self).__init__(**kwargs)
        self.row = row
        self.col = col
        self.game_state = game_state
        self.size_hint = (1, 1)
        self.is_on = False
        self.bind(on_touch_down=self.on_touch)

    def on_touch(self, instance, touch):
        if self.collide_point(*touch.pos):
            self.game_state.click(self.row, self.col)
            self.parent.refresh_buttons()
            self._update_win_check()
            return True
        return False

    def _update_win_check(self):
        if self.game_state.check_win():
            if self.game_state.timer_event:
                Clock.unschedule(self.game_state.timer_event)
                self.game_state.timer_event = None
            use_time = self.game_state.get_elapsed()
            best_step, best_t = self.game_state.best_record.get(
                GRID_SIZE, (float("inf"), float("inf"))
            )
            app = App.get_running_app()
            if self.game_state.current_steps < best_step or \
               (self.game_state.current_steps == best_step and use_time < best_t):
                self.game_state.best_record[GRID_SIZE] = (
                    self.game_state.current_steps, use_time
                )
                self.game_state.save_record()
            root = app.root
            if root:
                root.update_best_label(GRID_SIZE, self.game_state.best_record)
            content = BoxLayout(
                orientation='vertical', padding=20, spacing=10,
                size_hint=(1, 1)
            )
            content.add_widget(Label(
                text='步数: %d\n用时: %s' % (
                    self.game_state.current_steps,
                    root.format_time(use_time) if root else "?"
                ),
                halign='center', size_hint_y=0.6
            ))
            btn = Button(text='再来一局', size_hint_y=0.4)
            popup = Popup(title='游戏胜利', content=content, size_hint=(0.8, 0.45))
            btn.bind(on_press=lambda x: (popup.dismiss(), root.reset_game()))
            content.add_widget(btn)
            popup.open()

    def update_visual(self):
        self.canvas.clear()
        self.is_on = self.game_state.light_states[self.row][self.col]
        if self.is_on:
            bg_color = (0.98, 0.82, 0.14, 1)
        else:
            bg_color = (0.27, 0.27, 0.27, 1)
        with self.canvas:
            Color(*bg_color)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.15, 0.15, 0.15, 1)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=1)


class LightGrid(GridLayout):
    def __init__(self, game_state, **kwargs):
        super(LightGrid, self).__init__(**kwargs)
        self.cols = GRID_SIZE
        self.rows = GRID_SIZE
        self.game_state = game_state
        self.buttons = []
        self.spacing = 2
        self.padding = 2
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


class GameRoot(BoxLayout):
    def __init__(self, **kwargs):
        super(GameRoot, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [15, 15, 15, 15]
        self.spacing = 8
        try:
            self.game_state = GameState()
            self._build_ui()
            self.reset_game()
            self.update_best_label(GRID_SIZE, self.game_state.best_record)
            Clock.schedule_interval(self._timer_tick, 0.05)
        except Exception as e:
            log_error("GameRoot init ERROR: %s" % str(e))
            import traceback
            log_error(traceback.format_exc())

    def _build_ui(self):
        info_layout = BoxLayout(size_hint=(1, 0.09), spacing=5)
        self.step_label = Label(text="步数: 0", size_hint=(0.3, 1),
                                font_size='16sp')
        self.time_label = Label(text="用时: 00:00", size_hint=(0.4, 1),
                                font_size='16sp')
        self.best_label = Label(text="最佳: 暂无", size_hint=(0.3, 1),
                                font_size='14sp')
        info_layout.add_widget(self.step_label)
        info_layout.add_widget(self.time_label)
        info_layout.add_widget(self.best_label)
        self.add_widget(info_layout)

        self.grid = LightGrid(self.game_state, size_hint=(1, 0.82))
        self.add_widget(self.grid)

        btn_layout = BoxLayout(size_hint=(1, 0.09), spacing=10, padding=[0, 5, 0, 5])
        reset_btn = Button(text='重新开始', font_size='16sp')
        reset_btn.bind(on_press=lambda x: self.reset_game())
        btn_layout.add_widget(reset_btn)
        self.add_widget(btn_layout)

    def _timer_tick(self, dt):
        try:
            if self.game_state.start_time is not None:
                elapsed = self.game_state.get_elapsed()
                self.time_label.text = "用时: %s" % self.format_time(elapsed)
            self.step_label.text = "步数: %d" % self.game_state.current_steps
        except Exception as e:
            log_error("timer_tick error: %s" % str(e))

    def reset_game(self):
        self.game_state.reset_game()
        self.grid.refresh_buttons()
        self.step_label.text = "步数: 0"
        self.time_label.text = "用时: 00:00"

    def update_best_label(self, grid_size, best_record):
        best_step, best_t = best_record.get(grid_size, (float("inf"), float("inf")))
        if best_step != float("inf"):
            self.best_label.text = "最佳: %d步/%s" % (
                int(best_step), self.format_time(best_t)
            )
        else:
            self.best_label.text = "最佳: 暂无"

    @staticmethod
    def format_time(sec):
        m = int(sec // 60)
        s = int(sec % 60)
        return "%02d:%02d" % (m, s)


class GameApp(App):

    def build(self):
        try:
            return GameRoot()
        except Exception as e:
            log_error("App.build FATAL ERROR: %s" % str(e))
            import traceback
            log_error(traceback.format_exc())
            root = BoxLayout(orientation='vertical')
            root.add_widget(Label(text='Error! Check crash_log.txt', halign='center'))
            return root


if __name__ == "__main__":
    try:
        GameApp().run()
    except Exception as e:
        log_error("FATAL: %s" % str(e))
        import traceback
        log_error(traceback.format_exc())
        raise
