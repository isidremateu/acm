#:import Factory kivy.factory.Factory


Acquisition:
    name: 'Acquisition'
    fullscreen: True

    ScreenManager:
        id: sm

        Screen:
            name: 'Idle'
            canvas.before:
                Color:
                    rgb: .8, .2, .2
                Rectangle:
                    size: self.size
                
            AnchorLayout:
                Button:
                    size_hint: None, None
                    size: '150dp', '48dp'
                    text: 'Start Acquistion'
                    on_release: root.show_save()
        Screen:
            name: 'Acquisition'
            BoxLayout:
                orientation: 'vertical'
                BoxLayout:
                    orientation:'horizontal'
                    id: hor_layout1
                    size_hint_y: None
                    height: self.parent.height * 7 /8
           
                    BoxLayout:
                        orientation: 'vertical'
                        size_hint_x: 1
                        id: checkbox_layout
                        BoxLayout:
                            orientation: 'horizontal'
                            CheckBox:
                            Label:
                                size_hint_x:4
                                text: 'beta'
                        BoxLayout:
                            orientation: 'horizontal'
                            CheckBox:
                            Label:
                                size_hint_x:5
                                text: 'gamma'
                        BoxLayout:
                            orientation: 'horizontal'
                            CheckBox:
                            Label:
                                size_hint_x:5
                                text: 'sensor 1'
                        BoxLayout:
                            orientation: 'horizontal'
                            CheckBox:
                            Label:
                                size_hint_x:5
                                text: 'sensor 2'
                        BoxLayout:
                            orientation: 'horizontal'
                            CheckBox:
                            Label:
                                size_hint_x:5
                                text: 'sensor 3'
                        BoxLayout:
                            orientation: 'horizontal'
                            CheckBox:
                            Label:
                                size_hint_x:5
                                text: 'sensor 4'
                        BoxLayout:
                            orientation: 'horizontal'
                            CheckBox:
                            Label:
                                size_hint_x:5
                                text: 'sensor 5'
                        BoxLayout:
                            orientation: 'horizontal'
                            CheckBox:
                            Label:
                                size_hint_x:5
                                text: 'sensor 6'
        
                    BoxLayout:
                        id:plot_layout
                        orientation: 'vertical'
                        size_hint_x: 7
                        
                        #Label:
                        #    text: "Data plot here"
                        #    font_size: 10
                        # Add your matplotlib graph widget here
                        # For example, you can use a FigureCanvasKivyagg widget.
            
                BoxLayout:
                    orientation: 'horizontal'
                    id: hor_layout2
                    size_hint_y: None
                    height: self.parent.height * 1 /8
        
                    Label:
                        id: filename_label
                        text: 'File name here'
                        size_hint_x: 4
        
                    Button:
                        size_hint_x: 1
                        text: 'Stop Acquisition'
                        on_release: root.stop_acquisition()
