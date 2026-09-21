# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 12:39:53 2024

@author: Isidre
"""

import subprocess

def ping_subnet(subnet):
    for i in range(1, 255):
        ip = subnet + '.' + str(i)
        command = ['ping', '-n', '1', '-w', '100', ip]  # Adjust timeout (-w) as needed
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            print(f"Device found at IP address: {ip}")

subnet = '192.168.113'  # Specify your subnet here

ping_subnet(subnet)
