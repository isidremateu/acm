# -*- coding: utf-8 -*-
"""
Created on Thu Jan  4 12:19:19 2024

@author: Isidre
"""

from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemandmulti')

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
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg 
import matplotlib.pyplot as plt
from pancake import Pancake
from counting_code import gpio_counter 

from random import random

PLOT_REFRESH_PERIOD = 10 #s

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

    def __init__(self, **kwargs):
        super(Acquisition, self).__init__(**kwargs)

    def dismiss_popup(self):
        self._popup.dismiss()        

    def show_save(self):
        content = SaveDialog(save=self.start_acquisition, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content,
                        size_hint=(0.9, 0.9))
        self._popup.open()

    def updatePlot(self, xdata, ydata):
        self.ax.clear()
        
        for column in ydata.T:
            self.ax.plot(xdata, column)
            
        self.plot_canvas.figure = self.fig
        self.plot_canvas.draw()

    def start_acquisition(self, path, filename):
        
        sm = self.ids.sm 
        sm.current = 'Acquisition'
        filename_label = self.ids.filename_label
        filename_label. text = "Writing in: {}".format(filename)
        App.get_running_app().start_acquisition(filename)
        self.dismiss_popup()
        
        plot_layout = self.ids.plot_layout
        self.fig, self.ax = plt.subplots()
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        self.plot_canvas = FigureCanvasKivyAgg(figure = self.fig)
        self.ax.plot(x,y)
        plot_layout.add_widget(self.plot_canvas)

        
    def stop_acquisition(self):
       
        sm = self.ids.sm 
        sm.current = 'Idle'
        App.get_running_app().stop_acquisition()
        


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
                    sensor = Pancake()
                sensor.width = self.ids.sensors_layout.width/6
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
        self.root.ids.sm.switch_to(self.screens['Overview'])
        self.gpio = gpio_counter()
        self.gpio.start_gpio()
        Clock.schedule_interval(self.acquire_gpio, 1)

    def on_stop(self):
        
        if self.gpio.is_acquiring():self.gpio.stop_acquisition()
        self.gpio.stop_gpio()
        
    
    def start_acquisition(self, filename):
        print("START ACQUISITION")
        print("filename =", filename)
    
        self.start_acq_time = datetime.datetime.now()
        
        self.plot_refresh_every = max(int(PLOT_REFRESH_PERIOD / (self.gpio.get_Tcount()/1e6)),1)
    
        active_gpio = self.gpio.get_active_ports()
        self.file_to_write = filename
        with open(self.file_to_write, 'w') as file:
            file.write("active GPIO:{}\n".format(active_gpio))
            file.write("sampling period [us]: {:d}\n".format(self.gpio.get_sampling_period()))
            file.write("counting period [ms]: {:.3f}\n".format(self.gpio.get_Tcount()))
            file.write("acquisition start: {}\n".format(self.start_acq_time.strftime("%Y-%m-%d %H:%M:%S.%f")))
            file.write("\n")
            file.write("time[s]" + ''.join([", GPIO{}[counts]".format(gpio) for gpio in active_gpio]) + "\n")

        self.plot_data = np.array([[] for i in active_gpio]).T
        self.plot_time = np.array([])

        self.acquiring = True
        self.n0 = self.gpio.get_nread()
    
    
    
    
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

    def acquire_gpio(self,dt):
        
        active_gpio = self.gpio.get_active_ports().copy()
        active_gpio_gui = [sensor.get_gpio() for sensor in self.screens['Sensors'].ids.sensors_layout.children]
        active_gpio_gui = sorted(list(set(active_gpio_gui)))
        
        shielded = list()
        
        for port in active_gpio_gui:
            found = False
            for sensor in self.screens['Sensors'].ids.sensors_layout.children:
                if sensor.get_gpio() == port:
                    shielded.append(sensor.get_shielded())
                    found = True
                    break
                if found: break
        
        print("active gpio: ", active_gpio)
        print("active gpio_gui: ", active_gpio_gui)
        
        
        if active_gpio != active_gpio_gui:
            
            if self.gpio.is_acquiring(): self.gpio.stop_acquisition()
            
            for port in active_gpio:
                self.gpio.deactivate_port(port)
                
            print("active_ports after deactivate: ", self.gpio.get_active_ports().copy())
                
            for port in active_gpio_gui:
                self.gpio.activate_port(port)
            
            self.gpio.start_acquisition()

        else:
            if not self.gpio.is_acquiring(): self.gpio.start_acquisition()
        
        data = self.gpio.read_buffer()
        
        if len(data) > 0:
            Tc = self.gpio.get_Tcount()/1e6
            for sensor in self.screens['Sensors'].ids.sensors_layout.children:
                for rec, port in zip(data[-1], active_gpio_gui):
                    if sensor.get_gpio() == port: sensor.set_cps("{:.1f}".format(rec/Tc))
                    
            shielded = np.array(shielded)
            
            shielded_counts = np.array(data[-1])[shielded]
            unshielded_counts = np.array(data[-1])[~shielded]
            
            if (len(shielded_counts) > 0) and (len(unshielded_counts)>0):
                gamma = shielded_counts.mean() / Tc
                beta = unshielded_counts.mean() / Tc - gamma
                self.screens['Overview'].set_gamma("γ: {:.1f} cps".format(gamma))
                self.screens['Overview'].set_beta("β: {:.1f} cps".format(beta))

            if (len(shielded_counts) > 0) and (len(unshielded_counts)==0):
                gamma = shielded_counts.mean() / Tc
                self.screens['Overview'].set_gamma("γ: {:.1f} cps".format(gamma))
                self.screens['Overview'].set_beta("β: --.- cps")

            if (len(shielded_counts) == 0) and (len(unshielded_counts) > 0):
                gammabeta = unshielded_counts.mean() / Tc
                self.screens['Overview'].set_gamma("γ + β: {:.1f} cps".format(gammabeta))
                self.screens['Overview'].set_beta("----")



        
            if self.acquiring:
                nrec = self.gpio.get_nread() - len(data) - self.n0

                with open(self.file_to_write, 'a') as file:
                    for n, rec in enumerate(data):
                        file.write('{:.6f}'.format((nrec + n) * Tc) + "".join([", {:d}".format(entry) for entry in rec]) + "\n")
                        if (nrec + n)%self.plot_refresh_every == 0:
                            self.plot_data = np.concatenate((self.plot_data,np.array([rec])))
                            self.plot_time = np.concatenate((self.plot_time, [self.start_acq_time + datetime.timedelta(seconds = (nrec+n) * Tc)]))
                            self.screens['Acquisition'].updatePlot(self.plot_time, self.plot_data)
                print("Shape plot data:", self.plot_data.shape)


        self.gpio.flush_inactive(2)
        # for sensor in self.screens['Sensors'].ids.sensors_layout.children:
        #     sensor.set_cps('{:.1f}'.format(random()*int(sensor.get_gpio())))
 
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
    acmApp().run()