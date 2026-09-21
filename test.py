from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

Builder.load_string('''
<MyBoxLayout>:
    orientation: 'horizontal'

    MyWidget:
        size_hint_x: None
        width: self.parent.width / 6  # Set the width to 1/6 of the parent's width
        size_hint_y: 1

<MyWidget>:
    canvas:
        Color:
            rgba: 0, 1, 0, 1  # Green color for illustration
        Rectangle:
            pos: self.pos
            size: self.size


''')

class MyWidget(Widget):
    pass

class MyBoxLayout(BoxLayout):
    pass

class MyKivyApp(App):
    def build(self):
        return MyBoxLayout()

if __name__ == '__main__':
    MyKivyApp().run()
