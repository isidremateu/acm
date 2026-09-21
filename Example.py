# main.py

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class ExampleApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')

        label = Label(text='Enter a number between 1 and 40:')
        layout.add_widget(label)

        number_input = TextInput(multiline=False)
        number_input.bind(focus=self.on_focus_change)
        layout.add_widget(number_input)

        button = Button(text='Submit', on_press=self.submit_number)
        layout.add_widget(button)

        return layout

    def on_focus_change(self, instance, value):
        if not value:  # Check if the widget lost focus
            user_input = instance.text
            try:
                number = int(user_input)
                if 1 <= number <= 40:
                    print(f"Valid input: {number}")
                else:
                    print("Input must be between 1 and 40.")
                    instance.text = ''  # Clear the input
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                instance.text = ''  # Clear the input

    def submit_number(self, instance):
        number_input = self.root.children[1]  # Adjust the index based on your layout structure
        user_input = number_input.text

        try:
            number = int(user_input)
            if 1 <= number <= 40:
                print(f"Valid input: {number}")
            else:
                print("Input must be between 1 and 40.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

if __name__ == '__main__':
    ExampleApp().run()
