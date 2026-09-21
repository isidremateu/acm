# -*- coding: utf-8 -*-
"""
Created on Mon Mar 25 11:20:23 2024

@author: Isidre
"""

import pigpio
import time

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

if __name__ == "__main__":
    main()
