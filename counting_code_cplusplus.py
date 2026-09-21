# -*- coding: utf-8 -*-
"""
Created on Mon Mar 25 11:20:23 2024

@author: Isidre
"""
TEST = False


import numpy as np

# if not TEST: import pigpio
import time
import json
from os import system
import datetime
import os
import subprocess

NPORTS = 32
SAMPLE_RATE_AVAILABLE = [1,2,4,5,8,10]
MAX_TICKS = 4294967295
BUFFER_SIZE = 1000

spacebar = False

def update_output(header, data):
    # Clear the console
    system('cls' if os.name == 'nt' else 'clear')
    # Print each line
    for line in header:
        print(line)
    print(data)
    print("")
    print("(press the SPACE bar to stop acquisition)")


class gpio_counter:
    
    last_tick = np.zeros(NPORTS).astype(int)
    pi = None
    cb_list = [None for i in range(NPORTS)]
    buffer = np.zeros((NPORTS,BUFFER_SIZE)).astype(int)
    nwrite = np.zeros(NPORTS).astype(int)
    nread = 0
    active_gpio = list()
    sampling_period = 0
    start_tick = np.zeros(NPORTS).astype(int)
    carry = np.zeros(NPORTS).astype(int)
    Tc = 0
    acquiring = False
    start_acq_time = None
    
    # def callback_evt(self, gpio, level, tick):
    #     if tick < self.last_tick[gpio]:
    #         self.carry[gpio] = self.carry[gpio] +  int(np.floor((MAX_TICKS - self.start_tick[gpio]) / self.Tc))
    #         self.start_tick[gpio] =  - (MAX_TICKS - self.start_tick[gpio])%self.Tc
            
    #     # print("tick = ", tick)
    #     # print("start_tick=", self.start_tick[gpio])
    #     # print("Tc=", self.Tc)
    #     # print(np.floor((tick - self.start_tick[gpio])/self.Tc))

    #     nwrite = int(np.floor((tick - self.start_tick[gpio])/self.Tc)) + self.carry[gpio]
        
    #     # print("nwrite = ", nwrite)
        
    #     for i in range(nwrite - self.nwrite[gpio]):
    #         self.buffer[gpio][(self.nwrite[gpio]+i+1)%BUFFER_SIZE] = 0
            
    #     self.nwrite[gpio] = nwrite
    #     self.buffer[gpio][self.nwrite[gpio]%BUFFER_SIZE] +=1
    #     self.last_tick[gpio] = tick
            
    def read_buffer(self):
        
        if len(self.active_gpio) == 0: return []
        
        
        # Send a request to the C++ program
        self.process.stdin.write("GET\n")
        self.process.stdin.flush()

        # Read the response
        response = self.process.stdout.readline().strip()
        
        print("Received: {}".format(response))
        
        return([float(value) for n, value in enumerate(response.split(','))])
        
        
        
        
        
    def start_gpio(self, sampling_period = 5):
        self.sampling_period = sampling_period
        
    def activate_port(self, gpio):
        if gpio not in self.active_gpio:
            self.active_gpio.append(gpio)
            self.active_gpio = sorted(self.active_gpio)
            print("activating port {}".format(gpio))
            # self.pi.set_mode(gpio, pigpio.INPUT)
        
        
    def deactivate_port(self, gpio):
        print("deactivating port", gpio)
        print("active gpio before deletion", self.active_gpio)

        if gpio in self.active_gpio:
            self.active_gpio.remove(gpio)
        print("active gpio after deletion", self.active_gpio)

        
    def stop_gpio(self):
        pass
        # self.pi.stop()
        # system("sudo systemctl stop pigpiod")
        
    # def hardware_clock(self, gpio, Fs):
    #     self.pi.set_mode(gpio, pigpio.OUTPUT)
    #     self.pi.hardware_clock(gpio,Fs)
        
    def start_acquisition(self, Tcount = 1000, filename = None):
        

        # self.start_tick = np.ones(NPORTS).astype(int) * self.pi.get_current_tick()
        # self.last_tick = self.start_tick.copy()
        # self.buffer = np.zeros((NPORTS,BUFFER_SIZE)).astype(int)
        # self.nwrite = np.zeros(NPORTS).astype(int)
        # self.carry = np.zeros(NPORTS).astype(int)
        # self.nread = 0
        self.Tc = int(Tcount)
        self.start_acq_time = datetime.datetime.now()
        
        exec_line = ["sudo", "./counting-code"]
        
        if len(self.active_gpio) == 0: return
        
        for gpio in self.active_gpio:
            # self.cb_list[gpio] = self.pi.callback(gpio, pigpio.RISING_EDGE, self.callback_evt)
            exec_line.append(str(gpio))

        if not (filename == None):
            exec_line.append("-f")
            exec_line.append(filename)
            
        exec_line.append('-r')
        exec_line.append(str(self.Tc))
        exec_line.append('-s')
        exec_line.append(str(self.sampling_period))
        exec_line.append('-c')
                    
                
        
        print(exec_line)
        
        # Start the C++ program as a subprocess
        self.process = subprocess.Popen(
            exec_line,  # Path to your compiled C++ program
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        

        print("Start acquisition")

        self.acquiring = True
        
        # Read the response
        if not (filename == None):
            return self.process.stdout.readline().strip()
        
        
        
        
        
        
        
        

    def stop_acquisition(self): 
        print("Stop acquisition")
        self.acquiring = False        
        self.process.stdin.write("STOP\n")
        self.process.stdin.flush()
        time.sleep(1.0)
        
        self.process.terminate()
           
        # for gpio in self.active_gpio:
        #     self.cb_list[gpio].cancel()
            
    # def flush_inactive(self, depth):

    #     # nwritten = int(np.array([self.nwrite[gpio] for gpio in self.active_gpio]).max())
        
    #     nwritten = int(np.floor((datetime.datetime.now() - self.start_acq_time).total_seconds() / (self.Tc/1e6)))
        
    #     for gpio in self.active_gpio:
    #         for i in range(nwritten - self.nwrite[gpio]-depth):
    #             self.buffer[gpio][(self.nwrite[gpio]+i+1)%BUFFER_SIZE] = 0
    #         self.nwrite[gpio] = max(nwritten - depth, self.nwrite[gpio])
            
    def is_acquiring(self):
        return self.acquiring
    
    def get_active_ports(self):
        return self.active_gpio

    def get_Tcount(self):
        return self.Tc
    
    def get_sampling_period(self):
        return self.sampling_period


def read_config(filename):
    with open(filename, 'r') as file:
        config = json.load(file)

    data_file = config.get('data_file', '')
    active_gpio = config.get('active_gpio', [])
    sampling_frequency = config.get('sampling_frequency[kHz]', 0.0)
    counting_period = config.get('counting_period[ms]', 0.0)
    clock_gpio = config.get('clock_gpio', [])
    clock_frequency = config.get('clock_frequency[Hz]', 0.0)

    return data_file, active_gpio, sampling_frequency, counting_period, clock_gpio, clock_frequency


def main():
    global spacebar
    file_out, active_gpio, Fs, Tc, clk_gpio, Fs_clk = read_config("config.json")
    Ts = SAMPLE_RATE_AVAILABLE[np.argmin(abs(np.array(SAMPLE_RATE_AVAILABLE) - 1000/Fs))]
    Tc = round(Tc,3)
    
    
    # Initialize pigpio
    if not TEST:
        pi = gpio_counter()
        pi.start_gpio(Ts)

        for gpio in active_gpio:
            pi.activate_port(gpio)
            
        for gpio in clk_gpio:
            pi.hardware_clock(gpio,Fs_clk)
            
        pi.start_acquisition(Tc * 1000, filename=file_out)
        start_acq_time = datetime.datetime.now()


        while True:
            if not TEST: 
               
                print(pi.read_buffer())
                time.sleep(0.5)
           
  
    
    if not TEST:
        pi.stop_acquisition()
        pi.stop_gpio()

'''



# Pin numbers
input_pin = 22  # Change this to the GPIO pin number you're using for input
output_pin = 23  # Change this to the GPIO pin number you're using for output

# Initialize pigpio
pi = pigpio.pi()

# Set up input pin as input
pi.set_mode(input_pin, pigpio.INPUT)

# Set up output pin as output
pi.set_mode(output_pin, pigpio.OUTPUT)

# Define a function to count changes in logical levels
def count_changes(gpio, level, tick):
    global change_count
    change_count += 1

# Register the callback function for input_pin
cb = pi.callback(input_pin, pigpio.RISING_EDGE)

# Function to generate pulses on the output pin
def generate_pulses(period, duty_cycle, num_pulses):
    for _ in range(num_pulses):
        pi.write(output_pin, 1)  # Set output pin high
        time.sleep(period * duty_cycle)
        pi.write(output_pin, 0)  # Set output pin low
        time.sleep(period * (1 - duty_cycle))

# Main function
def main():
    global change_count
    change_count = 0

    # Parameters for pulse generation
    period = 0.1  # Period of the pulse train in seconds
    duty_cycle = 0.5  # Duty cycle of the pulse train
    num_pulses = 20  # Number of pulses to generate

    # Generate pulses on the output pin
    generate_pulses(period, duty_cycle, num_pulses)

    # Wait for a few seconds to allow counting
    time.sleep(2)

    # Print the number of changes counted
    print("Number of changes:", cb.tally())

    # Cancel callback
    cb.cancel()

    # Cleanup
    pi.stop()


'''
if __name__ == "__main__":
    main()
