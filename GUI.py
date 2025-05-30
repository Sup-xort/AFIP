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
import threading
import queue
import Sensor
import MODEL

rri_queue = queue.Queue()

def rri_reader():
    while True:
        rri = Sensor.get_rri()
        rri_queue.put(rri)

threading.Thread(target=rri_reader, daemon=True).start()

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

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bpm_data = []
        self.sample_count = 0
        self.valid_seq_count = 0
        self.bpm_event = None

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
        self.valid_seq_count = 0
        self.bpm_event = Clock.schedule_interval(self.update_bpm, 0.1)

    def update_bpm(self, dt):
        try:
            rri = rri_queue.get_nowait()
        except queue.Empty:
            return

        if not (200 < rri < 2100):
            self.valid_seq_count = 0
            return

        self.valid_seq_count += 1
        self.bpm_data.append(rri)

        bpm = round(60000 / rri)
        self.bpm_label.text = str(bpm)

        if len(self.bpm_data) > 50:
            self.bpm_data.pop(0)

        self.sample_count += 1
        self.graph.xmin = self.sample_count - 50
        self.graph.xmax = self.sample_count
        self.plot.points = [(self.sample_count - len(self.bpm_data) + i, 60000 / v)
                            for i, v in enumerate(self.bpm_data)]

        center = 60000 / self.bpm_data[0]
        self.graph.ymin = center - 15
        self.graph.ymax = center + 15

        if self.valid_seq_count >= 20:
            self.to_loading()

    def to_loading(self):
        if self.bpm_event:
            self.bpm_event.cancel()
        self.manager.get_screen('loading').receive_data(self.bpm_data[-20:])
        self.manager.current = 'loading'

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
        self.bpm_data = []

    def _update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def receive_data(self, bpm_data):
        self.bpm_data = bpm_data

    def on_enter(self):
        self.dot_index = 0
        self.event = Clock.schedule_interval(self.animate, 0.5)
        threading.Thread(target=self.run_prediction, daemon=True).start()

    def on_leave(self):
        if self.event:
            self.event.cancel()

    def animate(self, dt):
        self.label.text = self.dots[self.dot_index]
        self.dot_index = (self.dot_index + 1) % len(self.dots)

    def run_prediction(self):
        result, prob = MODEL.get_pred(self.bpm_data)
        Clock.schedule_once(lambda dt: self.pass_result(result, prob), 0)

    def pass_result(self, result, prob):
        result_screen = self.manager.get_screen('result')
        result_screen.set_result(result, prob)
        self.manager.current = 'result'

class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        self.layout = BoxLayout(orientation='vertical', padding=20)
        self.image_widget = Image(size_hint=(None, None), size=(150, 150))
        self.label = Label(text='', font_size='20sp', color=(0, 0, 0, 1))
        self.layout.add_widget(self.image_widget)
        self.layout.add_widget(self.label)
        self.add_widget(self.layout)

    def _update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def set_result(self, result, prob):
        if result == 0:
            self.image_widget.source = 'check.png'
            self.label.text = f"Normal rhythm\nConfidence: {prob*100:.1f}%"
        else:
            self.image_widget.source = 'warning.png'
            self.label.text = f"Irregular heartbeat\nConfidence: {prob*100:.1f}%"

        Clock.schedule_once(lambda dt: self.go_back_to_start(), 5.0)

    def go_back_to_start(self):
        self.manager.current = 'start'

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
