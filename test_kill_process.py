# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 09:04:02 2024

@author: Isidre
"""

import os
import subprocess
import psutil

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

# Example usage
process_name = "counting-code"
kill_process_by_name_as_sudo(process_name)
