import time
import os

# Function to update console output
def update_output(lines):
    # Clear the console
    os.system('cls' if os.name == 'nt' else 'clear')
    # Print each line
    for line in lines:
        print(line)

# Initial lines
line1 = "Line 1: Initial value"
line2 = "Line 2: Initial value"
line3 = "Line 3: Initial value"

# Update the console output
update_output([line1, line2, line3])
time.sleep(3)

# Modify the lines
line1 = "Line 1: Updated value"
line2 = "Line 2: Updated value"
line3 = "Line 3: Updated value"

# Update the console output with the modified lines
update_output([line1, line2, line3])

print("\nDone!")
