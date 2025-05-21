'''# main.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.button import Button
import random
import time
import threading
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.graphics import Color, Ellipse, Line

# ---- 가짜 심박수 시뮬레이터 ----
def get_fake_heart_rate():
    return 72 + random.randint(-5, 5)

# ---- 화면 구성 ----
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bpm = 0
        self.bpm_data = []

        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        self.layout.canvas.before.clear()

        with self.layout.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.layout.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        self.heart_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=120, spacing=20)
        self.heart_row.add_widget(Widget())

        self.heart_image_container = AnchorLayout(size_hint=(None, None), size=(130, 130))
        self.heart_image = Image(source='heart.png', size_hint=(None, None), size=(100, 100))
        self.heart_image_container.add_widget(self.heart_image)

        self.bpm_label = Label(text='92', font_size='80sp', color=(1, 0, 0, 1), size_hint=(None, None), size=(120, 100))

        self.heart_row.add_widget(self.heart_image_container)
        self.heart_row.add_widget(self.bpm_label)
        self.heart_row.add_widget(Widget())
        self.layout.add_widget(self.heart_row)

        self.graph = Graph(
            xlabel='', ylabel='',
            x_ticks_minor=0, x_ticks_major=0,
            y_ticks_major=0,
            y_grid_label=False, x_grid_label=False,
            padding=5, x_grid=False, y_grid=False,
            xmin=0, xmax=50, ymin=60, ymax=84,
            size_hint=(1, 0.7),
            border_color=[0.3, 0.3, 0.3, 1],
            draw_border=True,
            background_color=[1, 1, 1, 1]
        )
        self.plot = MeshLinePlot(color=[1, 0, 0, 1])
        self.graph.add_plot(self.plot)
        self.layout.add_widget(self.graph)
        self.add_widget(self.layout)

        self.dot_canvas = Widget()
        self.graph.add_widget(self.dot_canvas)

        Clock.schedule_interval(self.update_bpm, 0.5)
        Clock.schedule_once(self.to_loading_screen, 20)

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.layout.size
        self.bg_rect.pos = self.layout.pos

    def update_bpm(self, dt):
        self.bpm = get_fake_heart_rate()
        self.bpm_label.text = str(self.bpm)
        anim = Animation(size=(110, 110), duration=0.13) + Animation(size=(90, 90), duration=0.13)
        anim.start(self.heart_image)

        self.bpm_data.append(self.bpm)
        if len(self.bpm_data) > 50:
            self.bpm_data.pop(0)
        self.plot.points = [(i, v) for i, v in enumerate(self.bpm_data)]

        self.dot_canvas.canvas.clear()
        if self.bpm_data:
            i = len(self.bpm_data) - 1
            v = self.bpm_data[-1]

            graph = self.graph
            padding = graph.padding
            xmin, xmax = graph.xmin, graph.xmax
            ymin, ymax = graph.ymin, graph.ymax
            w, h = graph.width, graph.height
            gx, gy = graph.pos

            px = gx + padding + (w - 2 * padding) * ((i - xmin) / (xmax - xmin))
            py = gy + padding + (h - 2 * padding) * ((v - ymin) / (ymax - ymin))

            mid_y = gy + padding + (h - 2 * padding) * ((72 - ymin) / (ymax - ymin))

            with self.dot_canvas.canvas:
                Color(0, 0, 1, 1)
                Ellipse(pos=(px - 5, py - 5), size=(10, 10))
                Color(0.7, 0.7, 0.7, 1)
                Line(points=[gx + padding, mid_y, gx + w - padding, mid_y], width=1)

    def to_loading_screen(self, dt):
        self.manager.current = 'loading'

class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.loading_label = Label(text='.', font_size='40sp', color=(0, 0, 0, 1))
        self.layout.add_widget(self.loading_label)
        self.add_widget(self.layout)
        self.dots = ['.', '..', '...']
        self.dot_index = 0
        self.animation_event = None

        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def on_enter(self):
        self.animation_event = Clock.schedule_interval(self.animate_dots, 0.5)
        Clock.schedule_once(self.to_result_screen, 5)

    def on_leave(self):
        if self.animation_event:
            self.animation_event.cancel()

    def animate_dots(self, dt):
        self.loading_label.text = self.dots[self.dot_index]
        self.dot_index = (self.dot_index + 1) % len(self.dots)

    def to_result_screen(self, dt):
        self.manager.current = 'result'

class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = AnchorLayout()
        self.check_image = Image(source='check.png', size_hint=(None, None), size=(130, 130))
        layout.add_widget(self.check_image)
        self.add_widget(layout)

        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

class HeartApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(LoadingScreen(name='loading'))
        sm.add_widget(ResultScreen(name='result'))
        return sm

if __name__ == '__main__':
    HeartApp().run()'''

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.anchorlayout import AnchorLayout
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.graphics import Color, Rectangle
import random

# Fake BPM generator
def get_fake_bpm():
    return 72 + random.randint(-3, 3)

# Start Screen
class StartScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        layout = AnchorLayout()
        start_button = Button(
            text="Start Analysis",
            font_size='24sp',
            size_hint=(0.5, 0.2),
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1)
        )
        start_button.bind(on_press=self.start_analysis)
        layout.add_widget(start_button)
        self.add_widget(layout)

    def _update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def start_analysis(self, instance):
        self.manager.current = 'main'

# Main BPM Graph Screen
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bpm_data = []
        self.sample_count = 0

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        top_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=120, spacing=15)
        self.heart_image = Image(source='heart.png', size_hint=(None, None), size=(90, 90))
        self.bpm_label = Label(text='--', font_size='64sp', color=(0.5, 0.5, 0.5, 1), size_hint=(None, None), size=(120, 90))
        bpm_unit = Label(text='BPM', font_size='24sp', color=(0.4, 0.4, 0.4, 1), size_hint=(None, None), size=(60, 40))
        top_row.add_widget(Widget())
        top_row.add_widget(self.heart_image)
        top_row.add_widget(self.bpm_label)
        top_row.add_widget(bpm_unit)
        top_row.add_widget(Widget())

        self.graph = Graph(
            xlabel='', ylabel='',
            x_ticks_minor=0, x_ticks_major=0,
            y_ticks_major=0,
            y_grid_label=False, x_grid_label=False,
            padding=5, x_grid=False, y_grid=False,
            xmin=0, xmax=50, ymin=60, ymax=90,
            border_color=[0.9, 0.9, 0.9, 1],
            draw_border=True,
            background_color=[1, 1, 1, 1],
            size_hint=(1, 0.7)
        )
        self.plot = MeshLinePlot(color=[1, 0, 0, 1])
        self.graph.add_plot(self.plot)

        self.layout.add_widget(top_row)
        self.layout.add_widget(self.graph)
        self.add_widget(self.layout)

        Clock.schedule_interval(self.update_bpm, 0.3)
        Clock.schedule_once(self.to_loading, 10)

    def _update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def update_bpm(self, dt):
        bpm = get_fake_bpm()
        self.bpm_label.text = str(bpm)
        self.bpm_data.append(bpm)
        if len(self.bpm_data) > 50:
            self.bpm_data.pop(0)
        self.sample_count += 1
        self.graph.xmin = self.sample_count - 50
        self.graph.xmax = self.sample_count
        self.plot.points = [(self.sample_count - len(self.bpm_data) + i, v)
                            for i, v in enumerate(self.bpm_data)]

    def to_loading(self, dt):
        self.manager.current = 'loading'

# Loading screen
class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        layout = AnchorLayout()
        self.label = Label(text='Loading.', font_size='32sp', color=(0, 0, 0, 1))
        layout.add_widget(self.label)
        self.add_widget(layout)
        self.dot_index = 0
        self.dots = ['Loading.', 'Loading..', 'Loading...']
        self.event = None

    def _update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def on_enter(self):
        self.event = Clock.schedule_interval(self.animate, 0.5)
        Clock.schedule_once(self.to_result, 2)

    def on_leave(self):
        if self.event:
            self.event.cancel()

    def animate(self, dt):
        self.label.text = self.dots[self.dot_index]
        self.dot_index = (self.dot_index + 1) % len(self.dots)

    def to_result(self, dt):
        self.manager.current = 'result'

# Result screen
class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        layout = AnchorLayout()
        check_image = Image(source='check.png', size_hint=(None, None), size=(140, 140))
        layout.add_widget(check_image)
        self.add_widget(layout)

    def _update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

# App
class HeartApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(StartScreen(name='start'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(LoadingScreen(name='loading'))
        sm.add_widget(ResultScreen(name='result'))
        return sm

if __name__ == '__main__':
    HeartApp().run()
