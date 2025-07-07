import random
import os
import json
import requests
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle
from kivy.utils import platform
from kivy.config import Config
Config.set('graphics', 'dpi', 'auto')


# Android permissions
if platform == 'android':
    from android.permissions import request_permissions, Permission


message_map = {
    "P0101": "Mass or Volume Air Flow Circuit Range/Performance Problem",
    "P0102": "Mass or Volume Air Flow Circuit Low Input",
    "B1201": "Climate Control System Overload",
    "B1202": "Climate Control System Underload",
    "C0301": "Transfer Case Motor Circuit Low",
    "C0302": "Transfer Case Motor Circuit High",
    "U0101": "Lost Communication with TCM",
    "U0102": "Lost Communication with Transfer Case Control Module",
    "P0301": "Cylinder 1 Misfire Detected",
    "P0302": "Cylinder 2 Misfire Detected",
}

def send_json_file_to_ec2():
    url = "http://13.58.250.233:5000/upload-json"
    file_path = get_log_file_path()  # use the same path you save to

    try:
        with open(file_path, 'rb') as f:
            files = {'file': ('obd_log.json', f, 'application/json')}
            response = requests.post(url, files=files)
            print("✅ Server response:", response.json())
    except Exception as e:
        print("❌ Error uploading JSON file:", str(e))

def get_log_file_path():
    if platform == "android":
        # Direct path for User 10 — only works if app is running as User 10
        dir_path = "/storage/emulated/10/Download"
    else:
        dir_path = os.path.expanduser("~/obd_logs")
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, "obd_log.json")


def save_fault_to_log(code, message, timestamp):
    path = get_log_file_path()
    log_entry = {
        "time": timestamp,
        "Car_ID"   : "101",
        "Board" : "Infotainment",
        "Location" : "Egypt",
        "Error_Code": code
    }

    with open(path, "w") as f:
        json.dump([log_entry], f, indent=4)



class BubbleBox(BoxLayout):
    def __init__(self, code, message, timestamp, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=150, padding=(15, 10), spacing=5, **kwargs)
        with self.canvas.before:
            Color(0.2, 0.5, 0.9, 1)
            self.rect = RoundedRectangle(radius=[20], pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        message_label = Label(
            text=f"[{code}]: {message}", color=(1, 1, 1, 1), font_size= 35,
            halign='left', valign='middle', size_hint_y=None, height=30, text_size=(0, None)
        )
        message_label.bind(width=lambda l, w: setattr(l, 'text_size', (w - 10, None)))

        time_label = Label(
            text=timestamp, color=(1, 1, 1, 0.7), font_size=25,
            halign='right', valign='middle', size_hint_y=None, height=50, text_size=(0, None)
        )
        time_label.bind(width=lambda l, w: setattr(l, 'text_size', (w - 10, None)))

        self.add_widget(message_label)
        self.add_widget(time_label)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class PathBubble(BoxLayout):
    def __init__(self, path, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=100, padding=(15, 10), spacing=5, **kwargs)
        with self.canvas.before:
            Color(0.1, 0.7, 0.1, 1)
            self.rect = RoundedRectangle(radius=[20], pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        label = Label(
            text=f"Log File Path:\n{path}", color=(1, 1, 1, 1), font_size= 30,
            halign='left', valign='middle', text_size=(0, None),
            size_hint_y=None, height=60
        )
        label.bind(width=lambda l, w: setattr(l, 'text_size', (w - 10, None)))
        self.add_widget(label)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class CarDiagnosticApp(App):
    def build(self):
        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

        root_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        top_bar = BoxLayout(size_hint=(1, None), height=40)
        clear_button = Button(text="Clear", font_size=25, size_hint=(None, None), size=(150, 50),
                              background_normal='', background_color=(0.6, 0.6, 0.6, 1), color=(1, 1, 1, 1))
        clear_button.bind(on_press=self.clear_messages)
        top_bar.add_widget(clear_button)

        top_bar.add_widget(BoxLayout())

        exit_button = Button(text="EXIT", font_size=25, size_hint=(None, None), size=(150, 50),
                             background_normal='', background_color=(1, 0, 0, 1), color=(1, 1, 1, 1))
        exit_button.bind(on_press=lambda instance: App.get_running_app().stop())
        top_bar.add_widget(exit_button)

        self.scroll = ScrollView(size_hint=(1, 0.65))
        self.message_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.message_layout.bind(minimum_height=self.message_layout.setter('height'))
        self.scroll.add_widget(self.message_layout)

        self.button = Button(text="Examine my car", size_hint=(1, None), height=50, font_size=18)
        self.button.bind(on_press=self.examine_car)

        root_layout.add_widget(top_bar)
        root_layout.add_widget(self.scroll)
        root_layout.add_widget(self.button)

        log_path = get_log_file_path()
        self.message_layout.add_widget(PathBubble(path=log_path))

        return root_layout

    def examine_car(self, instance):
        # Ensure only one error message is generated
        num_messages = 1  # Always generate 1 message
        available_codes = list(message_map.keys())
        
        # Select a random error code
        selected_codes = random.sample(available_codes, min(num_messages, len(available_codes)))

        if num_messages == 0:
            timestamp = datetime.now().strftime("%I:%M %p %d-%m-%y")
            bubble = BubbleBox(code="INFO", message="No diagnostic issues found.", timestamp=timestamp)
            self.message_layout.add_widget(bubble)
            save_fault_to_log("INFO", "No diagnostic issues found.", timestamp)
        else:
            for code in selected_codes:
                timestamp = datetime.now().strftime("%I:%M %p %d-%m-%y")
                message = message_map[code]
                bubble = BubbleBox(code=code, message=message, timestamp=timestamp)
                self.message_layout.add_widget(bubble)
                save_fault_to_log(code, message, timestamp)
        send_json_file_to_ec2()


    def clear_messages(self, instance):
        self.message_layout.clear_widgets()
        # Optional: Clear log file
        # os.remove(get_log_file_path())


if __name__ == "__main__":
    CarDiagnosticApp().run()
