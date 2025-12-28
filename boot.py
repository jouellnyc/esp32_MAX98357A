import storage

# This tells CircuitPython: 
# "Give the MICROCONTROLLER write access, and make it Read-Only for the PC"
storage.remount("/", False)
