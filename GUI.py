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
import Sensor
import MODEL
import random

# Fake BPM generator
def get_fake_bpm():
    return 72 + random.randint(-3, 3)

# Placeholder for model decision
def model_predict(bpm_data):
    if len(bpm_data) == 0:
        return 0
    avg = sum(bpm_data) / len(bpm_data)
    return 1 if avg > 80 else 0

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
        self.manager.get_screen('main').start_measurement()
        self.manager.current = 'main'

# Main BPM Graph Screen
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bpm_data = []
        self.sample_count = 0
        self.bpm_event = None
        self.to_loading_event = None

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
        self.plot.line_width = 2
        self.graph.add_plot(self.plot)

        self.layout.add_widget(top_row)
        self.layout.add_widget(self.graph)
        self.add_widget(self.layout)

    def _update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def start_measurement(self):
        self.bpm_data = []
        self.sample_count = 0
        self.bpm_event = Clock.schedule_interval(self.update_bpm, 0.3)
        self.to_loading_event = Clock.schedule_once(self.to_loading, 10)

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

        if self.bpm_data:
            center = self.bpm_data[0]
            self.graph.ymin = center - 15
            self.graph.ymax = center + 15

    def to_loading(self, dt):
        if self.bpm_event:
            self.bpm_event.cancel()
        if self.to_loading_event:
            self.to_loading_event.cancel()
        self.manager.get_screen('loading').receive_data(self.bpm_data)
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

    def receive_data(self, bpm_data):
        self.result_code = model_predict(bpm_data)

    def on_enter(self):
        self.event = Clock.schedule_interval(self.animate, 0.5)
        Clock.schedule_once(self.pass_result, 2.0)

    def on_leave(self):
        if self.event:
            self.event.cancel()

    def animate(self, dt):
        self.label.text = self.dots[self.dot_index]
        self.dot_index = (self.dot_index + 1) % len(self.dots)

    def pass_result(self, dt):
        self.manager.get_screen('result').set_result(self.result_code)
        self.manager.current = 'result'

# Result screen
class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        self.layout = AnchorLayout()
        self.image_widget = Image(size_hint=(None, None), size=(150, 150))
        self.layout.add_widget(self.image_widget)
        self.add_widget(self.layout)

    def _update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def set_result(self, result):
        if result == 0:
            self.image_widget.source = 'check.png'
        else:
            self.image_widget.source = 'danger.png'

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
