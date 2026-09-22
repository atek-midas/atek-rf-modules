<p align="center">
  <img src="UI/logo_new-300x86.png" alt="ATEK MIDAS" width="300">
</p>

<h1 align="center">ATEK RF Modules</h1>

<p align="center">
  Common STM32 firmware and a cross-platform desktop user interface for ATEK MIDAS RF modules.
</p>

---

## Pre-built Application Downloads

Pre-built Windows and Linux packages are distributed through the public release repository:

**[Download ATEK RF Modules UI](https://github.com/sydundar/atek-rf-modules-ui-releases/releases/latest)**

This repository contains the application and firmware development sources.  
End users who only need the desktop application should use the release repository above.


## Overview

This repository contains:

- A common embedded firmware project for multiple ATEK MIDAS RF modules
- A cross-platform desktop user interface
- Module datasheets
- Windows and Linux executable build scripts
- Embedded UI assets such as the ATEK MIDAS logo and module datasheets

The connected RF module identifies itself over USB CDC. The desktop application detects the module automatically and loads the appropriate control interface.

The firmware uses a common source code base. The target RF module is selected before compiling the firmware.

---

## Features

### Embedded Firmware

- Common firmware architecture for multiple RF modules
- STM32 USB CDC communication
- Automatic module identification using the `*IDN?` command
- RF state control using serial commands
- Hardware button control
- SSD1306 OLED display support
- Module state synchronization with the desktop UI
- Support for entering the STM32 system bootloader
- Module-specific GPIO and DAC control
- Compile-time target module selection

### Desktop User Interface

- Cross-platform Python application
- Windows and Linux executable build scripts
- Automatic serial port detection
- Automatic connected-module identification
- Module-specific control panels
- Real-time TX and RX logging
- Hardware state synchronization
- Embedded PDF datasheet viewer
- Demo mode
- Dark industrial user interface
- Thread-safe serial communication

---

## Supported RF Modules

| Module | Description | Control Type |
|---|---|---|
| ATEK256N3 | LF–20 GHz absorptive SPDT switch | 2-state digital control |
| ATEK357P4 | LF–20 GHz 5-bit digital attenuator | 32-state digital control |
| ATEK366P5 | 2–18 GHz 180° analog phase shifter | DAC control |
| ATEK1601 / ATEK656N5 | 2–18 GHz sub-octave USB-controlled filter bank | 6-state digital control |
| ATEK1801 / ATEK888P5 | 20–530 MHz 32-state USB-controlled low-pass filter | 32-state digital control |
| ATEK950P6 | 485–8000 MHz switchable filter bank | 8-state digital control |

> The desktop UI identifies ATEK1601 hardware using the `ATEK656N5` device ID and ATEK1801 hardware using the `ATEK888P5` device ID.

> Verify the GPIO mapping and target-board hardware revision before compiling or deploying a firmware variant.

---

## Repository Structure

```text
atek-rf-modules/
├── firmware/
│   ├── Core/
│   ├── Drivers/
│   ├── USB_DEVICE/
│   ├── RF_MODULES_MAIN.ioc
│   └── ...
│
├── UI/
│   ├── ATEK_RF_MODULES_USER_INTERFACE_v1.0.py
│   ├── ATEK_RF_MODULES_USER_INTERFACE_v2.0.py
│   ├── ConvertFilestoBase64.py
│   ├── assets.py
│   ├── ATEK_MIDAS.ico
│   ├── logo_new-300x86.png
│   ├── build_win.bat
│   └── build_lin.sh
│
├── datasheets/
│   ├── ATEK256N3.pdf
│   ├── ATEK357P4.pdf
│   ├── ATEK366P5.pdf
│   ├── ATEK656N5.pdf
│   ├── ATEK888P5.pdf
│   └── ATEK950P6.pdf
│
├── README.md
├── LICENSE
└── .gitignore
```

---

# Firmware

## Target Platform

The current firmware project is configured for:

| Item | Configuration |
|---|---|
| Microcontroller | STM32F070C6T6 |
| MCU family | STM32F0 |
| Package | LQFP48 |
| System clock | 48 MHz |
| Development environment | STM32CubeIDE |
| STM32Cube firmware package | STM32Cube FW F0 |
| USB interface | USB Device CDC Full Speed |
| Display interface | I2C |
| Display controller | SSD1306 |
| Debug interface | SWD |

---

## Selecting the Target Module

The firmware uses one common source code base for all supported RF modules.

In the current implementation, the target module is selected in:

```text
firmware/Core/Src/main.c
```

Locate the following line:

```c
RF_Init(ATEK888P5);
```

Replace the argument with one of the supported module definitions:

```c
RF_Init(ATEK256N3);
RF_Init(ATEK357P4);
RF_Init(ATEK366P5);
RF_Init(ATEK656N5);
RF_Init(ATEK888P5);
RF_Init(ATEK950P6);
```

Only one module must be selected for each firmware build.

Example:

```c
RF_Init(ATEK357P4);
```

This builds the firmware for the ATEK357P4 digital attenuator.

---

## Building the Firmware

1. Open STM32CubeIDE.
2. Import the project from the `firmware/` directory.
3. Select the target module in `main.c`.
4. Clean the project.
5. Build the project using the required configuration.
6. Program the generated firmware into the target STM32 device.

Depending on the STM32CubeIDE project configuration, the generated files may include:

```text
.elf
.bin
.hex
.map
```

Build output is normally generated inside the selected STM32CubeIDE build configuration directory, such as:

```text
firmware/Debug/
```

or:

```text
firmware/Release/
```

The exact output files depend on the active STM32CubeIDE build settings.

---

## Firmware Communication Protocol

The firmware communicates with the desktop UI over USB CDC.

Commands are terminated using carriage return, line feed, or both.

### Identify Device

Request:

```text
*IDN?
```

Example response:

```text
ATEK888P5
```

### Read Current State

Request:

```text
GET?
```

Example response:

```text
STATE:5
```

### Set Module State

Request:

```text
SET:<state>
```

Example:

```text
SET:5
```

The valid state range depends on the selected module.

### Enter STM32 System Bootloader

Command:

```text
SET:UPDATE
```

The firmware disconnects the USB CDC interface and jumps to the STM32 ROM bootloader.

> The current desktop UI provides module control and monitoring. A complete firmware flashing workflow is not currently included in the UI.

---

# Desktop User Interface

## Requirements

Running the application directly from Python requires:

- Python 3
- CustomTkinter
- PySerial
- Pillow

Install the required packages with:

```bash
python -m pip install customtkinter pyserial pillow
```

---

## Running from Source

From the repository root:

### Windows

```bat
python UI\ATEK_RF_MODULES_USER_INTERFACE_v2.0.py
```

### Linux

```bash
python3 UI/ATEK_RF_MODULES_USER_INTERFACE_v2.0.py
```

---

## Connecting a Module

1. Connect the ATEK RF module to the computer using USB.
2. Start the desktop application.
3. Select the detected serial port.
4. Select the required baud rate.
5. Click **CONNECT**.
6. The application sends the following identification command:

```text
*IDN?
```

7. The connected module returns its device ID.
8. The application automatically loads the correct control panel.
9. The current hardware state is requested using:

```text
GET?
```

The default baud-rate selection in the UI is:

```text
115200
```
 

---

## Demo Mode

The UI includes a demo mode for automatic state cycling.

Demo mode operates only when:

- A serial connection is active
- A supported module has been identified
- A module control panel is loaded
- Demo mode is enabled

While active, the UI automatically advances the module state at regular intervals.

---

## Embedded Assets

The desktop UI loads the ATEK MIDAS logo and PDF datasheets from:

```text
UI/assets.py
```

The assets are stored as Base64-encoded data, allowing them to be included in packaged executable distributions.

The source PDF files remain available separately in:

```text
datasheets/
```

The `ConvertFilestoBase64.py` utility is intended for regenerating the embedded asset data when logos or datasheets are updated.

---

# Building the Desktop Application

The supplied scripts automatically:

- Check for Python
- Install the required Python packages
- Install PyInstaller
- Remove previous build outputs
- Build the application using PyInstaller
- Disable UPX compression
- Generate a directory-based executable package

The application is built using PyInstaller's `--onedir` mode.

This means the executable must be distributed together with the other files in its generated directory.

---

## Windows Executable

Open Command Prompt or Git Bash and run:

```bat
UI\build_win.bat
```

The build script creates:

```text
UI\dist\ATEK_RF_MODULES_UI\
```

The Windows executable is:

```text
UI\dist\ATEK_RF_MODULES_UI\ATEK_RF_MODULES_UI.exe
```

Distribute the entire directory:

```text
UI\dist\ATEK_RF_MODULES_UI\
```

Do not distribute only the `.exe` file.

The Windows build uses:

- Directory-based packaging
- No UPX compression
- No console window
- ATEK MIDAS application icon, when available

---

## Linux Executable

First, make the build script executable:

```bash
chmod +x UI/build_lin.sh
```

Run the script:

```bash
./UI/build_lin.sh
```

The build script creates:

```text
UI/dist/ATEK_RF_MODULES_UI/
```

The Linux executable is:

```text
UI/dist/ATEK_RF_MODULES_UI/ATEK_RF_MODULES_UI
```

Distribute the entire directory:

```text
UI/dist/ATEK_RF_MODULES_UI/
```

Do not distribute only the executable file.

---

## Build Output Directories

The following directories are generated automatically and should not be committed:

```text
UI/build/
UI/dist/
UI/venv/
```

PyInstaller may also generate temporary `.spec` files. These files are ignored by the repository configuration.

---

## Development Notes

- Version 2.0 is the current desktop UI entry point.
- Version 1.0 is retained as a previous implementation reference.
- The build scripts expect the UI source file, `assets.py`, logo, and icon to remain in the same `UI/` directory.
- The desktop application uses a background serial communication thread.
- UI updates are passed safely to the main application thread.
- Datasheets are opened using the operating system's default PDF viewer.
- The application supports Windows, Linux, and macOS source execution, although executable build scripts are currently supplied only for Windows and Linux.

---

## License

- **Source code** (firmware sources written by ATEK MIDAS, Python API,
  desktop UI, examples, build scripts): MIT License, see `LICENSE`.
- **Third-party components** (STM32 HAL, CMSIS, STM32 USB Device Library,
  SSD1306 driver, Python packages) remain under their own licenses,
  see `THIRD_PARTY_NOTICES.md`.
- **Datasheets, manuals, the ATEK MIDAS name and logo** are not covered by
  the MIT License. © ATEK MIDAS, all rights reserved.
for the complete license text.

---

## Disclaimer

This software is provided without warranty.

Users are responsible for:

- Verifying the selected RF module configuration
- Confirming target-board pin assignments
- Confirming output-state behavior
- Validating generated firmware before deployment
- Following the electrical limits specified in the applicable module datasheet
- Confirming compatibility with their own hardware and operating environment

---

## Copyright

Copyright © 2026 ATEK MIDAS. All rights reserved where not otherwise granted by the MIT License.
