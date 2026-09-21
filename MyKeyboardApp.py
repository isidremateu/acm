# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 16:45:28 2024

@author: Isidre
"""
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemandmulti')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.button import Button

class MyTextInput(TextInput):
    def __init__(self, **kwargs):
        super(MyTextInput, self).__init__(**kwargs)
        # Disable the native keyboard
        self.keyboard_mode = 'managed'
        # Enable the on-screen keyboard
        self.input_type = 'text'

class MyKeyboardApp(App):
    def build(self):
        # Set up the main layout
        layout = BoxLayout(orientation='vertical')

        # Add the text input widget
        text_input = MyTextInput()
        layout.add_widget(text_input)

        # Add a button to clear the text input
        clear_button = Button(text='Clear')
        clear_button.bind(on_press=lambda instance: text_input.text_input.clear())
        layout.add_widget(clear_button)

        return layout

if __name__ == '__main__':
    Window.size = (400, 200)  # Set window size
    MyKeyboardApp().run()
