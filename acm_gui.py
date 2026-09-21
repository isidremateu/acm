from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

class MyApp(App):
    def build(self):
        # Create a BoxLayout as the root widget
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Create a TextInput widget
        self.text_input = TextInput(font_size=20, multiline=False)

        # Create a Button widget
        button = Button(text='Press me!', on_press=self.on_button_press)

        # Add widgets to the layout
        layout.add_widget(self.text_input)
        layout.add_widget(button)

        return layout

    def on_button_press(self, instance):
        # Update the text_input when the button is pressed
        self.text_input.text = 'Hello world'

if __name__ == '__main__':
    MyApp().run()
