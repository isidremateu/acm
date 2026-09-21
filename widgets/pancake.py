# -*- coding: utf-8 -*-
"""
Created on Wed Jan  3 12:01:57 2024

@author: Isidre
"""
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

from kivy.uix.boxlayout import BoxLayout

from kivy.properties import StringProperty, BooleanProperty, NumericProperty

from kivy.base import runTouchApp
from kivy.lang import Builder 

Builder.load_string(''' 

                    
<Pancake>:
    
    size_hint_x: None
    #width: self.parent.width / 6  # Set the width to 1/6 of the parent's width
    size_hint_y: 1
    orientation:'vertical'
    gpio:gpio_in.gpio
    Label:
        text: 'GPIO'
    GpioInput:
        id:gpio_in
        input_type: 'number'
        #input_filter: lambda text, from_undo: (text if text.isdigit() and 1 <= int(text) <= 40 else '1')
        hint_text: "Enter a number between 1 and 40"
        multiline: False
        keyboard_mode: 'auto'
        # on_text: self.parent.update_gpio()
        #on_focus: self.parent.on_focus
    
    Label: 
        text: "Shielded"
    Switch:
        id: boolean_switch
        active: root.shielded
        on_active: root.on_shielded_switch_active(boolean_switch.active)
    Label:
        text: "CPS"
    Label:
        text: root.cps


''')     

class GpioInput(TextInput):
    gpio = NumericProperty()
    def on_focus(self, instance, value):
        if not value:  # Check if the widget lost focus
            user_input = instance.text
            try:
                number = int(user_input)
                if 0 <= number <= 39:
                    print(f"Valid input: {number}")
                    self.gpio = int(number)
                    print("gpio updated to: ", self.gpio)
                else:
                    print("Input must be between 0 and 39.")
                    instance.text = ''  # Clear the input
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                instance.text = ''  # Clear the input
                
    def get_gpio(self):
        return self.gpio


class Pancake(BoxLayout):
    cps = StringProperty('')
    shielded = BooleanProperty(False)
    # gpio = StringProperty()
    gpio = NumericProperty(0)    
    # def update_gpio(self):
    #     self.gpio = self.ids.gpio_in.text
    #     print("gpio text: ", self.ids.gpio_in.text)


    def __init__(self, gpio_value=1, shielded = False, **kwargs):
        super(Pancake, self).__init__(**kwargs)
        # Add any code you want to execute upon creation of the widget here
        self.ids.gpio_in.gpio = gpio_value
        self.ids.gpio_in.text = str(gpio_value)
        self._shielded = shielded  # Use an internal variable to avoid recursion
        self.ids.boolean_switch.active = shielded
        
        
    
    def get_gpio(self):
        # print("Pancake gpio: ", self.gpio)
        # print("gpio in: ", self.ids.gpio_in.gpio)
        return self.ids.gpio_in.gpio

    def set_cps(self, cps):
        # print("set cps", cps)
        try:
            self.cps = cps
        except Exception as e:
            # Handle the exception and display information
            print(f"An error occurred: {type(e).__name__} - {str(e)}")
    
    def on_shielded_switch_active(self, value):
        if self._shielded != value:
            self._shielded = value
            self.shielded = value  # This line will not cause a recursive loop
        print(f"Boolean value: {self.shielded}")

    def get_shielded(self):
        return self._shielded

if __name__ == '__main__':
    runTouchApp(Pancake())