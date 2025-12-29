import storage

# This tells CircuitPython: 
# "Give the MICROCONTROLLER write access, and make it Read-Only for the PC"
storage.remount("/", False)

import supervisor
supervisor.runtime.autoreload = False


import storage

# This hides the CIRCUITPY drive from the host computer (Linux/Windows/Mac)
storage.disable_usb_drive()

print("USB Drive Disabled")

