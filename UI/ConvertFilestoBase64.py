"""
===========================================================================
===========================================================================
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 ATEK MIDAS
===========================================================================
===========================================================================
"""

# Run this script ONCE to generate your assets.py file
import base64
import os

# Put your actual file names here. You can add icon PNGs here too.
files_to_convert = [
    "logo_new-300x86.png",
    "ATEK888P5.pdf", "ATEK950P6.pdf", "ATEK656N5.pdf",
    "ATEK256N3.pdf", "ATEK357P4.pdf", "ATEK366P5.pdf"
]

with open("assets.py", "w") as out_file:
    out_file.write("ASSETS = {\n")
    for filename in files_to_convert:
        if os.path.exists(filename):
            with open(filename, "rb") as file:
                b64_string = base64.b64encode(file.read()).decode('utf-8')
                out_file.write(f'    "{filename}": "{b64_string}",\n')
        else:
            print(f"Warning: {filename} not found in folder.")
    out_file.write("}\n")

print("Success! 'assets.py' has been generated.")