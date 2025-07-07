# main.py (Frontend + Backend merged)
import sys
import socket
import threading
import json
import pickle
import numpy as np
import torch
import pygame
from gtts import gTTS
import speech_recognition as sr
import os
import random
from tensorflow.keras.models import load_model
from transformers import BertTokenizer, BertForSequenceClassification




from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior


class IconButton(ButtonBehavior, Image):
    allow_stretch = True
    keep_ratio = True
    pass

Window.clearcolor = (0, 0, 0, 1)

class ChatBubble(Label):
    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.size_hint_y = None
        self.halign = 'left' if not is_user else 'right'
        self.valign = 'middle'
        self.text_size = (Window.width * 0.7, None)
        self.padding = (15, 10)
        self.color = (0, 0, 0, 1)
        self.font_size = 14
        self.markup = True
        self.bind(texture_size=self.setter('size'))
        with self.canvas.before:
            Color(0.7, 0.9, 1, 1) if not is_user else Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(radius=[15])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class ChatApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect(('127.0.0.1', 5800))
            print("Connected to chatbot backend.")
        except Exception as e:
            print(f"Could not connect to backend: {e}")

    def on_new_chat(self, instance):
        self.chat_layout.clear_widgets()

    def on_model_change(self, spinner, text):
        try:
            self.client_socket.send((text.lower() + "\n").encode())
        except Exception as e:
            print(f"Failed to switch model: {e}")

    def build(self):
        self.title = "Chatbot"
        root = BoxLayout(orientation='vertical', padding=10, spacing=5)

        top = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10, padding=(10, 5))

        model_spinner = Spinner(text='LLM', values=('LLM', 'LSTM'), size_hint=(None, None), size=(100, 40))
        model_spinner.bind(text=self.on_model_change)
        top.add_widget(model_spinner)
        top.add_widget(Widget())
        top.add_widget(Button(text='New Chat', size_hint=(None, None), size=(100, 40), font_size=18, on_press=self.on_new_chat))
        root.add_widget(top)

        self.chat_layout = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=(0, 10))
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.chat_layout)
        root.add_widget(scroll)

        bottom = BoxLayout(size_hint_y=None, height=50, spacing=10)
        listen_btn = Button(text='Listen', size_hint=(None, None), size=(100, 40))
        listen_btn.bind(on_press=self.on_listen_press)
        bottom.add_widget(listen_btn)

        self.input = TextInput(hint_text='Ask anything', multiline=False, size_hint_y=None, height=40)
        self.input.bind(on_text_validate=self.on_send)
        bottom.add_widget(self.input)

        mic_btn = IconButton(source='microphone.png', size_hint=(None, None), size=(40, 40), on_press=self.on_mic_press , on_release=self.on_mic_release)
        bottom.add_widget(mic_btn)
        root.add_widget(bottom)

        return root

    def on_send(self, instance):
        msg = self.input.text.strip()
        if msg == "":
            return
        self.add_message(msg, is_user=True)
        try:
            self.client_socket.send((msg + "\n").encode())
            response = self.client_socket.recv(1024).decode().strip()
        except Exception as e:
            response = f"[Error] {e}"
        self.add_message(response, is_user=False)
        self.input.text = ""

    def on_mic_press(self, instance):
        try:
            self.client_socket.send(("start recording\n").encode())
            response = self.client_socket.recv(1024).decode().strip()
            self.add_message(" " + response, is_user=False)
        except Exception as e:
            self.add_message(f"[Mic Error] {e}", is_user=False)




    def on_mic_release(self, instance):
       try:
            self.client_socket.send(("stop recording\n").encode())
            response = self.client_socket.recv(1024).decode().strip()

            if response.startswith("AUDIO_TEXT:"):
                voice_text = response.replace("AUDIO_TEXT:", "").strip()
                self.input.text = voice_text
                self.on_send(self.input)  #  call on_send with simulated text
            else:
               self.add_message(" " + response, is_user=False)

       except Exception as e:
                self.add_message(f"[Mic Release Error] {e}", is_user=False)

            
    def on_listen_press(self, instance):
        try:
            self.client_socket.send(("toggle tts\n").encode())
            response = self.client_socket.recv(1024).decode().strip()
            self.add_message(" " + response, is_user=False)
        except Exception as e:
            self.add_message(f"[Toggle Error] {e}", is_user=False)


         
    def add_message(self, msg, is_user):
        bubble = ChatBubble(text=msg, is_user=is_user)
        self.chat_layout.add_widget(bubble)

# ========== BACKEND THREAD LAUNCHER ==========

def start_backend():
    # This function contains the same code as in chat.py
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import backend.chat as backend

if __name__ == '__main__':
    threading.Thread(target=start_backend, daemon=True).start()
    ChatApp().run()
