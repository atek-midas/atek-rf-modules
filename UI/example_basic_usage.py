"""
ATEK RF Modules - basic API example

Place this file in the same folder as atek_rf_modules_scpi_api.py and run:
    python example_basic_usage.py                 (finds the module automatically)
    python example_basic_usage.py COM5            (Windows, fixed port)
    python example_basic_usage.py /dev/ttyACM0    (Linux, fixed port)
"""

import sys
import atek_rf_modules_scpi_api as atek

if len(sys.argv) > 1:
    port = sys.argv[1]
else:
    devices = atek.find_devices()                 # sends *IDN? to every serial port
    if not devices:
        sys.exit("No ATEK module found.")
    port = devices[0].port

with atek.connect(port) as dev:
    print("Port  :", port)
    print("IDN   :", dev.identify())      # *IDN?
    dev.set_state(3)                      # SET:3
    print("State :", dev.get_state())     # GET?