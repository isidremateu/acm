# -*- coding: utf-8 -*-
"""
Created on Thu Jan  4 12:19:19 2024

@author: Isidre
"""

from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemandmulti')
Config.set('graphics','show_cursor','0')
Config.write()

import sys
sys.path.append('widgets')
import datetime
import numpy as np
from os.path import dirname, join
from kivy.uix.button import Button
from kivy.app import App
from kivy.clock import Clock
from time import time
from kivy.properties import NumericProperty, StringProperty, BooleanProperty,\
    ListProperty
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup

from kivy.core.window import Window
from kivy.uix.checkbox import CheckBox
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg 
import matplotlib.pyplot as plt
from widgets.pancake import Pancake
from counting_code_cplusplus import gpio_counter 

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
import psutil
import os
from random import random

DEFAULT_GPIO = [5,6,13,19,21,26]
DEFAULT_SHIELDED = [True,False,False,True,False,False]
PLOT_REFRESH_PERIOD = 10 #s


# Get the 'tab10' colormap
colormap = plt.get_cmap('tab10')

# Retrieve the colors
trace_colors = [colormap(i) for i in range(colormap.N)]

# # Define the colors and their grayed-out versions
# trace_colors = [
#     (183/255, 28/255, 28/255, 1),  # Dark Red
#     (27/255, 94/255, 32/255, 1),   # Dark Green
#     (13/255, 71/255, 161/255, 1),  # Dark Blue
#     (245/255, 127/255, 23/255, 1), # Dark Orange
#     (74/255, 20/255, 140/255, 1),  # Dark Purple
#     (0/255, 105/255, 92/255, 1),   # Dark Cyan
#     (66/255, 66/255, 66/255, 1),   # Dark Grey
#     (62/255, 39/255, 35/255, 1)    # Dark Brown
# ]

gray_color = [0.7, 0.7, 0.7, 1]

MAX_BUFFER = 100


def kill_process_by_name_as_sudo(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] == process_name:
                pid = proc.info['pid']
                # Use sudo to kill the process
                command = f"sudo kill -9 {pid}"
                os.system(command)
                # Alternatively, using subprocess:
                # subprocess.run(['sudo', 'kill', '-9', str(pid)])
                print(f"Killed process {process_name} with PID {pid} using sudo")
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    print(f"No process named {process_name} was found.")
    return False




class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class ShowcaseScreen(Screen):
    # fullscreen = BooleanProperty(False)

    def add_widget(self, *args):
        if 'content' in self.ids:
            return self.ids.content.add_widget(*args)
        return super(ShowcaseScreen, self).add_widget(*args)
    
    
class Overview(ShowcaseScreen):
    
    def set_gamma(self, text):
        self.ids.gamma_label.text = text
        
    def set_beta(self, text):
        self.ids.beta_label.text = text


class Acquisition(ShowcaseScreen):

    fig = None
    ax = None
    plot_canvas = None
    active_traces = None

    def __init__(self, **kwargs):
        super(Acquisition, self).__init__(**kwargs)

    def dismiss_popup(self, instance):
        print("dismissing popup")
        self._popup.dismiss()        

    # def show_save(self):
    #     content = SaveDialog(save=self.start_acquisition, cancel=self.dismiss_popup)
    #     self._popup = Popup(title="Save file", content=content,
    #                     size_hint=(0.9, 0.9))
    #     self._popup.open()

    def show_save(self):
        # Create a BoxLayout to hold the TextInput and buttons
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Add a Label
        label = Label(text="Enter file name:")
        layout.add_widget(label)
        
        # Create a TextInput for the file name
        self.filename_input = TextInput(text = "acm", multiline=False, hint_text="File name")
        layout.add_widget(self.filename_input)
        
        # Create a BoxLayout for the buttons
        button_layout = BoxLayout(orientation='horizontal', spacing=10)
        
        # Add a Confirm button
        confirm_button = Button(text="Confirm")
        confirm_button.bind(on_release=self.on_confirm)
        button_layout.add_widget(confirm_button)
        
        # Add a Cancel button
        cancel_button = Button(text="Cancel")
        cancel_button.bind(on_release=self.dismiss_popup)
        button_layout.add_widget(cancel_button)
        
        # Add the button layout to the main layout
        layout.add_widget(button_layout)
        
        # Create the Popup
        self._popup = Popup(title="Save file", content=layout,
                            size_hint=(0.9, 0.5))  # Adjust size_hint as needed
        self._popup.open()

    def on_confirm(self, instance):
        # Get the file name entered by the user
        file_name = self.filename_input.text
        
        file_name = file_name.split(',')[0]
       
        self._popup.dismiss()
        
        # Call the start_acquisition method with the file path
                
        sm = self.ids.sm 
        sm.current = 'Acquisition'
  
        # Delay the addition of widgets to ensure the screen is fully loaded
        Clock.schedule_once(lambda dt:self.start_acquisition(file_name), 0.05)
  
        # self.start_acquisition(file_name)
        
        # Close the popup

    # def dismiss_popup(self, instance):
    #     # Close the popup
    #     self._popup.dismiss()






    def updatePlot(self, xdata, ydata):
        self.ax.clear()
        
        n=0
        for column, active in zip(ydata.T, self.active_traces):
            if active: self.ax.plot(xdata, column, color = trace_colors[n], lw=3)
            
            n+=1
        
        self.ax.set_ylabel("CPS")
        self.plot_canvas.figure = self.fig
        self.plot_canvas.draw()

    def start_acquisition(self, filename):

        plot_layout = self.ids.plot_layout
        self.fig, self.ax = plt.subplots()
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        self.plot_canvas = FigureCanvasKivyAgg(figure = self.fig)
        self.ax.plot(x,y)
        plot_layout.add_widget(self.plot_canvas)
        
        
        active_gpio, shielded = App.get_running_app().get_active_gpio()        
        checkbox_layout = self.ids.checkbox_layout
        
        
        screen_height = Window.height
        # Define font size as a fraction of the screen height
        font_size = screen_height * 0.05  # 5% of screen height
        
        checkbox_labels = [Label(text='GPIO_{:d}{:s}'.format(gpio,'*' if sh else ''), size_hint = [1,1], font_size = font_size) for gpio, sh in zip(active_gpio, shielded)]
        if shielded.sum() > 0: 
            checkbox_labels.append(Label(text="γ", size_hint = [1,1], font_size = font_size))
            if shielded.sum() < len(shielded): 
                checkbox_labels.append(Label(text="β",size_hint = [1,1], font_size = font_size))
                self.active_traces = [(len(checkbox_labels) - i) < 3 for i in range(len(checkbox_labels))]
            else:
                self.active_traces = [(len(checkbox_labels) - i) < 2 for i in range(len(checkbox_labels))]

        else:
            self.active_traces = [True for i in checkbox_labels]
        
        for n, label in enumerate(checkbox_labels):
            
       
            # Attach the inded to the checkbox for easy reference
            label.trace_index = n
            label.color = trace_colors[n] if self.active_traces[n] else gray_color
            label.bind(on_touch_down=self.on_click)

           # Add the sensor layout to the main layout
            checkbox_layout.add_widget(label)
        
        filename_label = self.ids.filename_label
        full_name = App.get_running_app().start_acquisition(filename)
        filename_label.text = "Writing in: {}".format(full_name)    
        
    def on_click(self, instance, touch):
        
        if instance.collide_point(*touch.pos):
            self.active_traces[instance.trace_index] = not self.active_traces[instance.trace_index] 
            if  self.active_traces[instance.trace_index] :
                instance.color = trace_colors[instance.trace_index]
            else:
                instance.color = gray_color
    def stop_acquisition(self):
       
        sm = self.ids.sm 
        sm.current = 'Idle'
        App.get_running_app().stop_acquisition()
        plot_layout = self.ids.plot_layout
        plot_layout.remove_widget(self.plot_canvas)
        self.ids.checkbox_layout.clear_widgets()


class Sensors(ShowcaseScreen):
    
    hidden_sensors = ListProperty([])
    
    def __init__(self, **kwargs):
        super(Sensors, self).__init__(**kwargs)
    
    # def on_kv_post(self, base_widget):
    #     Clock.schedule_once(self.initialize_sensors, 0.1)
        
    # def initialize_sensors(self, dt):
    
    #     self.update_sensors()
        
    def update_sensors(self):
        sensors = self.ids.sensors_layout.children
        N = int(self.ids.sensors_slider.value)
        if N > len(sensors):
            for i in range(len(sensors),N):
                if len(self.hidden_sensors) > 0:
                    sensor = self.hidden_sensors.pop()
                else:
                    sensor = Pancake(gpio_value=DEFAULT_GPIO[i], shielded = DEFAULT_SHIELDED[i])
                # sensor.width = self.ids.sensors_layout.width/6
                sensor.width = Window.width/6
                self.ids.sensors_layout.add_widget(sensor)
        
        if N < len(sensors):
            for i in range(len(sensors),N,-1):
                sensor = sensors[0]
                self.ids.sensors_layout.remove_widget(sensor)
                self.hidden_sensors.append(sensor)
                

class acmApp(App):

    index = NumericProperty(-1)
    current_title = StringProperty()
    time = NumericProperty(0)
    screen_names = ListProperty([])
    hierarchy = ListProperty([])
    gpio = None
    file_to_write = None
    start_acq_time = None
    acquiring = False
    n0 = 0
    plot_refresh_every = 1
    plot_time = None
    
    plot_data = None
    
    def build(self):
        self.title = 'Air Contamination Monitor'
        # Clock.schedule_interval(self._update_clock, 1 / 60.)
        self.screens = {}
        self.screen_names = ['Overview', 'Sensors', 'Acquisition']
        curdir = dirname(__file__)
        self.available_screens = [join(curdir, 'data', 'screens',
            '{}.kv'.format(fn).lower()) for fn in self.screen_names]
        # self.go_next_screen()
        for i in range(len(self.screen_names)):
            self.load_screen(i)
        # self.root.ids.sm.switch_to(self.screens['Sensors'])

        self.root.ids.sm.switch_to(self.screens['Overview'])
        self.gpio = gpio_counter()
        self.gpio.start_gpio()
        Clock.schedule_once(self.set_defaults, 1)
        Clock.schedule_interval(self.acquire_gpio, 1)

    def set_defaults(self, dt):
        
        self.screens['Sensors'].ids.sensors_slider.value = 6


    def on_stop(self):
        
        if self.gpio.is_acquiring():self.gpio.stop_acquisition()
        self.gpio.stop_gpio()
        
    
    def start_acquisition(self, filename):
        
        if self.gpio.is_acquiring():self.gpio.stop_acquisition()
        


        print("START ACQUISITION")
        print("filename =", filename)
    
        full_name = self.gpio.start_acquisition(filename = filename)
    
    
        self.start_acq_time = datetime.datetime.now()
        
        # self.plot_refresh_every = max(int(PLOT_REFRESH_PERIOD / (self.gpio.get_Tcount()/1e6)),1)
    
        active_gpio = self.active_gpio
        # self.file_to_write = filename
        # with open(self.file_to_write, 'w') as file:
        #     file.write("active GPIO:{}\n".format(active_gpio))
        #     file.write("sampling period [us]: {:d}\n".format(self.gpio.get_sampling_period()))
        #     file.write("counting period [ms]: {:.3f}\n".format(self.gpio.get_Tcount()))
        #     file.write("acquisition start: {}\n".format(self.start_acq_time.strftime("%Y-%m-%d %H:%M:%S.%f")))
        #     file.write("\n")
        #     file.write("time[s]" + ''.join([", GPIO{}[counts]".format(gpio) for gpio in active_gpio]) + "\n")

        self.plot_data = [[] for i in active_gpio]
        if self.shielded.sum() > 0: self.plot_data.append([])
        if self.shielded.sum() < len(self.shielded): self.plot_data.append([])
        self.plot_data = np.array(self.plot_data).T
        self.plot_time = np.array([])

        self.acquiring = True
        
        self.refresh_period = 0.5
        
        return full_name
    
    
    # def update_gui(self,dt):
    #     self.active_sensors.clear()
    #     for sensor in self.screens['Sensors'].ids.sensors_layout.children:
    #         self.active_sensors.append(
    #             {'gpio':sensor.get_gpio(),
    #              'shielded':sensor.get_shielded()})
                
        # if 'Acquisition' in self.screens.keys():
        #     for sensor in self.active_sensors:
                
        #         sensor.set_cps('{:.1f}'.format(random()*int(sensor.get_gpio())))
 
    def stop_acquisition(self):
        self.acquiring = False
        self.gpio.stop_acquisition()
        self.gpio.start_acquisition()


    def check_sensors_settings(self):
        active_gpio = self.gpio.get_active_ports().copy()
        active_gpio_gui = [sensor.get_gpio() for sensor in self.screens['Sensors'].ids.sensors_layout.children]
        shielded = [sensor.get_shielded() for sensor in self.screens['Sensors'].ids.sensors_layout.children]

        if len(active_gpio_gui)>0:

            # Initialize new lists to remove duplicates
            filtered_gpio = []
            filtered_shielded = []
            
            # Iterate over both lists simultaneously
            for i in range(len(active_gpio_gui)):
                if active_gpio_gui[i] not in filtered_gpio:
                    filtered_gpio.append(active_gpio_gui[i])
                    filtered_shielded.append(shielded[i])
                    
            combined = zip(filtered_gpio, filtered_shielded)
            
            # Sort the combined list based on the first list (filtered_gpio)
            sorted_combined = sorted(combined)
            
            # Unzip the sorted list back into two lists
            active_gpio_gui, shielded = zip(*sorted_combined)
            
            # Convert the tuples back to lists if needed
            active_gpio_gui = list(active_gpio_gui)
            shielded = list(shielded)
       
        if active_gpio != active_gpio_gui:
            
            if self.gpio.is_acquiring(): self.gpio.stop_acquisition()
            
            for port in active_gpio:
                self.gpio.deactivate_port(port)
                
            for port in active_gpio_gui:
                self.gpio.activate_port(port)
            
            self.gpio.start_acquisition()

        else:
            if not self.gpio.is_acquiring(): self.gpio.start_acquisition()

        self.active_gpio = np.array(active_gpio_gui)
        self.shielded = np.array(shielded)

    def get_active_gpio(self):
        return self.active_gpio, self.shielded

    def acquire_gpio(self,dt):
        
        self.check_sensors_settings()
        
        if self.gpio.is_acquiring():
        
            data = self.gpio.read_buffer()
        
        
            if len(data) > 0:
                time = data[0]
                data = data[1:]
    
                Tc = self.gpio.get_Tcount()/1e3
                for rec, sensor in zip(data, self.screens['Sensors'].ids.sensors_layout.children):
                    sensor.set_cps("{:.1f}".format(rec/Tc))
                
                shielded_counts = np.array(data)[self.shielded]
                unshielded_counts = np.array(data)[~self.shielded]
                
                if (len(shielded_counts) > 0) and (len(unshielded_counts)>0):
                    gamma = shielded_counts.mean() / Tc
                    beta = unshielded_counts.mean() / Tc - gamma
                    self.screens['Overview'].set_gamma("γ: {:.1f} cps".format(gamma))
                    self.screens['Overview'].set_beta("β: {:.1f} cps".format(beta))
                    data = np.append(data, gamma)
                    data = np.append(data, beta)
    
                if (len(shielded_counts) > 0) and (len(unshielded_counts)==0):
                    gamma = shielded_counts.mean() / Tc
                    self.screens['Overview'].set_gamma("γ: {:.1f} cps".format(gamma))
                    self.screens['Overview'].set_beta("β: --.- cps")
                    data = np.append(data, gamma)
    
                if (len(shielded_counts) == 0) and (len(unshielded_counts) > 0):
                    gammabeta = unshielded_counts.mean() / Tc
                    self.screens['Overview'].set_gamma("γ + β: {:.1f} cps".format(gammabeta))
                    self.screens['Overview'].set_beta("----")

                if self.acquiring:
                    
                    if len(self.plot_data) > MAX_BUFFER: self.resample_data()
                    
                    if len(self.plot_time)>0:
                        current_time = self.start_acq_time + datetime.timedelta(seconds = time)
                        last_time = self.plot_time[-1]
                        if current_time - last_time < datetime.timedelta(seconds = self.refresh_period): return
                    
                    self.plot_data = np.concatenate((self.plot_data,np.array([data])))
                    self.plot_time = np.concatenate((self.plot_time, [self.start_acq_time + datetime.timedelta(seconds = time)]))
                    self.screens['Acquisition'].updatePlot(self.plot_time, self.plot_data)
                    
                    print("Shape plot data:", self.plot_data.shape)
                        
        # for sensor in self.screens['Sensors'].ids.sensors_layout.children:
        #     sensor.set_cps('{:.1f}'.format(random()*int(sensor.get_gpio())))
 
    def resample_data(self):
        self.refresh_period = 2*self.refresh_period
        # Iterate over the list starting from the second element
        keep_array = np.zeros_like(self.plot_time).astype(bool)
        
        current_time = self.plot_time[0]
        for n, dt in enumerate(self.plot_time[1:],1):
            if dt >= current_time + datetime.timedelta(seconds=self.refresh_period):
                keep_array[n] = True
                current_time = dt

        self.plot_time = self.plot_time[keep_array]
        self.plot_data = self.plot_data[keep_array,:]
        
 
    def on_pause(self):
        return True

    def on_resume(self):
        pass

    # def on_current_title(self, instance, value):
    #       self.root.ids.spnr.text = value
    #       # self.go_screen(value)

    def go_previous_screen(self):
        self.index = (self.index - 1) % len(self.available_screens)
        # screen = self.load_screen(self.index)
        # sm = self.root.ids.sm
        # sm.switch_to(screen, direction='right')
        self.root.ids.spnr.text = self.screen_names[self.index]

    def go_hierarchy_previous(self):
        ahr = self.hierarchy
        if len(ahr) == 1:
            return
        if ahr:
            ahr.pop()
        if ahr:
            idx = ahr.pop()
            self.go_screen(idx)

    def go_next_screen(self):
        self.index = (self.index + 1) % len(self.available_screens)
        # screen = self.load_screen(self.index)
        # sm = self.root.ids.sm
        # sm.switch_to(screen, direction='left')
        self.root.ids.spnr.text = self.screen_names[self.index]
        
    def go_screen(self, idx):
        self.index = idx
        screen = self.load_screen(idx)
        self.root.ids.sm.switch_to(screen)
        self.current_title = screen.name
        
    def load_screen(self, index):
        if self.screen_names[index] in self.screens:
            return self.screens[self.screen_names[index]]
        screen = Builder.load_file(self.available_screens[index])
        self.screens[self.screen_names[index]] = screen
        return screen

    def _update_clock(self, dt):
        self.time = time()    
        
        

#     def showcase_floatlayout(self, layout):

#         def add_button(*t):
#             if not layout.get_parent_window():
#                 return
#             if len(layout.children) > 5:
#                 layout.clear_widgets()
#             layout.add_widget(Builder.load_string('''
# #:import random random.random
# Button:
#     size_hint: random(), random()
#     pos_hint: {'x': random(), 'y': random()}
#     text:
#         'size_hint x: {} y: {}\\n pos_hint x: {} y: {}'.format(\
#             self.size_hint_x, self.size_hint_y, self.pos_hint['x'],\
#             self.pos_hint['y'])
# '''))
#             Clock.schedule_once(add_button, 1)
#         Clock.schedule_once(add_button)

#     def showcase_boxlayout(self, layout):

#         def add_button(*t):
#             if not layout.get_parent_window():
#                 return
#             if len(layout.children) > 5:
#                 layout.orientation = 'vertical'\
#                     if layout.orientation == 'horizontal' else 'horizontal'
#                 layout.clear_widgets()
#             layout.add_widget(Builder.load_string('''
# Button:
#     text: self.parent.orientation if self.parent else ''
# '''))
#             Clock.schedule_once(add_button, 1)
#         Clock.schedule_once(add_button)

#     def showcase_gridlayout(self, layout):

#         def add_button(*t):
#             if not layout.get_parent_window():
#                 return
#             if len(layout.children) > 15:
#                 layout.rows = 3 if layout.rows is None else None
#                 layout.cols = None if layout.rows == 3 else 3
#                 layout.clear_widgets()
#             layout.add_widget(Builder.load_string('''
# Button:
#     text:
#         'rows: {}\\ncols: {}'.format(self.parent.rows, self.parent.cols)\
#         if self.parent else ''
# '''))
#             Clock.schedule_once(add_button, 1)
#         Clock.schedule_once(add_button)

#     def showcase_stacklayout(self, layout):
#         orientations = ('lr-tb', 'tb-lr',
#                         'rl-tb', 'tb-rl',
#                         'lr-bt', 'bt-lr',
#                         'rl-bt', 'bt-rl')

#         def add_button(*t):
#             if not layout.get_parent_window():
#                 return
#             if len(layout.children) > 11:
#                 layout.clear_widgets()
#                 cur_orientation = orientations.index(layout.orientation)
#                 layout.orientation = orientations[cur_orientation - 1]
#             layout.add_widget(Builder.load_string('''
# Button:
#     text: self.parent.orientation if self.parent else ''
#     size_hint: .2, .2
# '''))
#             Clock.schedule_once(add_button, 1)
#         Clock.schedule_once(add_button)

#     def showcase_anchorlayout(self, layout):

#         def change_anchor(self, *l):
#             if not layout.get_parent_window():
#                 return
#             anchor_x = ('left', 'center', 'right')
#             anchor_y = ('top', 'center', 'bottom')
#             if layout.anchor_x == 'left':
#                 layout.anchor_y = anchor_y[anchor_y.index(layout.anchor_y) - 1]
#             layout.anchor_x = anchor_x[anchor_x.index(layout.anchor_x) - 1]

#             Clock.schedule_once(change_anchor, 1)
#         Clock.schedule_once(change_anchor, 1)


Factory.register('SaveDialog', cls=SaveDialog)



if __name__ == '__main__':
    
    Window.show_cusor = False  # Hide the mouse cursor
    Window.fullscreen = 'auto'         # Optional: Set fullscreen mode
        
    kill_process_by_name_as_sudo('counting-code')
    acmApp().run()