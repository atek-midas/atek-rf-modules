<p align="center">
  <img src="UI/logo_new-300x86.png" alt="ATEK MIDAS" width="300">
</p>

<h1 align="center">ATEK RF Modules</h1>

<p align="center">
  Common STM32 firmware, a Python control API and a cross-platform desktop user interface for ATEK MIDAS RF modules.
</p>

---

## Pre-built Application Downloads

Ready-to-run Windows and Linux packages are published on the Releases page of this repository:

**[Download ATEK RF Modules UI](https://github.com/atek-midas/atek-rf-modules/releases/latest)**

| Package | System requirements |
|---|---|
| `ATEK_RF_MODULES_UI_v<version>_windows_x64.zip` | Windows 10 or 11, 64-bit |
| `ATEK_RF_MODULES_UI_v<version>_linux_x64.tar.gz` | 64-bit Linux, glibc 2.35 or newer (e.g. Ubuntu 22.04 and later) |

No Python installation is required.

**Windows:** extract the zip file and run `ATEK_RF_MODULES_UI.exe` from the extracted folder.

**Linux:**

```bash
tar -xzf ATEK_RF_MODULES_UI_v<version>_linux_x64.tar.gz
./ATEK_RF_MODULES_UI/ATEK_RF_MODULES_UI
```

On Linux, the user needs access to the serial port. If the module cannot be opened, run the following command once and log out and back in:

```bash
sudo usermod -aG dialout $USER
```

Keep the extracted folder together; the executable alone does not run. If the application reports an unexpected error, it saves the details to `error_log.txt`; please include this file when contacting ATEK MIDAS support.

## Overview

This repository contains:

- A common embedded firmware project for multiple ATEK MIDAS RF modules
- A Python API for controlling the modules from your own software
- A cross-platform desktop user interface built on that API
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
- State change reporting (`STATE:<n>`) for synchronization with connected software
- Support for entering the STM32 system bootloader (USB DFU)
- Module-specific GPIO control
- Compile-time target module selection

### Python API

- Single file, only requires `pyserial`
- Automatic module identification and module-specific classes
- Range checking and confirmation of every state change
- Background reader thread with state-change callbacks
- Automatic port discovery

### Desktop User Interface

- Cross-platform Python application built on the Python API
- Windows and Linux executable build scripts
- Automatic serial port detection
- Automatic connected-module identification
- Module-specific control panels
- Real-time TX and RX logging
- Hardware state synchronization, including front-panel button changes
- Embedded PDF datasheet viewer
- Demo mode (hidden by default)
- About window with version and license information

---

## Supported RF Modules

| Module (`*IDN?` response) | RF chip | Description | States |
|---|---|---|---|
| ATEK1801 | ATEK888P5 | 20–550 MHz 32-state USB-controlled low-pass filter | 32 |
| ATEK1601 | ATEK656N5 | 2–18 GHz sub-octave USB-controlled filter bank | 6 |
| ATEK950P6 | ATEK950P6 | 485–8500 MHz switchable filter bank (7 bands + bypass) | 8 |
| ATEK357P4 | ATEK357P4 | LF–20 GHz 5-bit digital attenuator | 32 |
| ATEK256N3 | ATEK256N3 | LF–20 GHz absorptive SPDT switch | 2 |
| ATEK366P5 | ATEK366P5 | 2–18 GHz 180° analog phase shifter | 101 |

> The **Module** name is the identifier returned by the `*IDN?` command. The **RF chip** is the device used inside the module; the datasheets in `datasheets/` are named after the RF chip.

> DAC control for the ATEK366P5 analog phase shifter is not yet implemented in the firmware.

> Verify the GPIO mapping and target-board hardware revision before compiling or deploying a firmware variant.

---

## Repository Structure

```text
atek-rf-modules/
├── firmware/
│   ├── Core/
│   ├── Drivers/
│   ├── Middlewares/
│   ├── USB_DEVICE/
│   ├── RF_MODULES_MAIN.ioc
│   └── ...
│
├── UI/
│   ├── ATEK_RF_MODULES_USER_INTERFACE.py   # Desktop application
│   ├── atek_rf_modules_scpi_api.py         # Python API
│   ├── example_basic_usage.py              # API example
│   ├── ConvertFilestoBase64.py
│   ├── assets.py
│   ├── ATEK_MIDAS.ico
│   ├── logo_new-300x86.png
│   ├── build_win.bat
│   └── build_lin.sh
│
├── datasheets/
│   ├── README.md
│   ├── ATEK256N3.pdf
│   ├── ATEK357P4.pdf
│   ├── ATEK366P5.pdf
│   ├── ATEK656N5.pdf
│   ├── ATEK888P5.pdf
│   └── ATEK950P6.pdf
│
├── .github/
│   └── workflows/
│       └── release.yml                     # Automated Windows/Linux builds and releases
│
├── README.md
├── LICENSE
├── THIRD_PARTY_NOTICES.md
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
RF_Init(ATEK1601);
```

Replace the argument with one of the supported module definitions:

```c
RF_Init(ATEK1801);
RF_Init(ATEK1601);
RF_Init(ATEK950P6);
RF_Init(ATEK357P4);
RF_Init(ATEK256N3);
RF_Init(ATEK366P5);
```

Only one module must be selected for each firmware build.

Example:

```c
RF_Init(ATEK1801);
```

This builds the firmware for the ATEK1801 tunable low-pass filter module.

---

## Building the Firmware

1. Open STM32CubeIDE.
2. Import the project from the `firmware/` directory.
3. Select the target module in `main.c`.
4. Clean the project.
5. Build the project using the required configuration.
6. Program the generated firmware into the target STM32 device (SWD, or USB DFU as described below).

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

The firmware communicates over USB CDC (virtual serial port). The baud rate setting has no effect on a USB CDC link.

Commands are ASCII, case-sensitive and terminated using carriage return, line feed, or both.

| Command | Description | Response |
|---|---|---|
| `*IDN?` | Returns the module name | e.g. `ATEK1801` |
| `GET?` | Returns the current state index | `STATE:<n>` |
| `SET:<n>` | Selects state `n` | `STATE:<n>` if accepted, nothing if `n` is out of range |
| `SET:UPDATE` | Enters the STM32 system bootloader | `Entering DFU Mode...`, then USB disconnects |

### State Reporting

The module sends `STATE:<n>` whenever its state changes, regardless of the source:

- after an accepted `SET:<n>` command,
- after a change made with the front-panel buttons,
- as the response to `GET?`.

Software should therefore accept `STATE:<n>` lines at any time. The Python API handles this automatically.

### Firmware Update (USB DFU)

`SET:UPDATE` places the module in the factory ROM bootloader of the STM32 (USB DFU mode). New firmware can then be loaded over USB with STM32CubeProgrammer or `dfu-util`, without using the BOOT0 pin. Disconnect and reconnect the USB cable after programming to start the new firmware.

> The desktop UI does not include a firmware flashing workflow.

---

# Python API

`UI/atek_rf_modules_scpi_api.py` is a single-file Python API for the modules. It can be used without the desktop UI.

## Installation

```bash
python -m pip install pyserial
```

Copy `atek_rf_modules_scpi_api.py` into the folder of your script and import it.

## Quick Start

```python
import atek_rf_modules_scpi_api as atek

with atek.connect("COM5") as dev:       # "/dev/ttyACM0" on Linux
    print(dev.identify())                # *IDN?
    dev.set_state(1)                     # SET:1, waits for confirmation
    print(dev.get_state())               # GET?
```

`atek.find_devices()` scans the serial ports and returns the connected ATEK modules. `atek.connect()` returns a module-specific class, for example `atek.TunableLowPassFilter` for the ATEK1801 or `atek.ATEK1601` for the ATEK1601, with methods such as `set_band()` and `set_frequency_mhz()`.

A complete example is provided in `UI/example_basic_usage.py`:

```bash
python UI/example_basic_usage.py          # finds the module automatically
python UI/example_basic_usage.py COM5     # fixed port
```

---

# Desktop User Interface

## Requirements

Running the application directly from Python requires:

- Python 3.8 or newer
- CustomTkinter
- PySerial
- Pillow

Install the required packages with:

```bash
python -m pip install customtkinter pyserial pillow
```

The application uses `atek_rf_modules_scpi_api.py`, which must remain in the same `UI/` directory.

---

## Running from Source

From the repository root:

### Windows

```bat
python UI\ATEK_RF_MODULES_USER_INTERFACE.py
```

### Linux

```bash
python3 UI/ATEK_RF_MODULES_USER_INTERFACE.py
```

---

## Connecting a Module

1. Connect the ATEK RF module to the computer using USB.
2. Start the desktop application.
3. Select the detected serial port.
4. Click **CONNECT**.
5. The application identifies the module with `*IDN?` and loads the matching control panel.
6. The current hardware state is read with `GET?`; the module is not reset when connecting.

Changes made with the front-panel buttons are reported by the module and shown in the UI automatically.

---

## Demo Mode

The UI includes a demo mode for automatic state cycling. The switch is hidden by default; set `SHOW_DEMO_MODE_BUTTON = True` in `ATEK_RF_MODULES_USER_INTERFACE.py` to show it.

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
- Copy `LICENSE` and `THIRD_PARTY_NOTICES.md` into the package

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

Build on the oldest Linux distribution you want to support: the package runs on the build distribution and newer ones, but not on older ones.

---

## Automated Builds and Releases

The workflow in `.github/workflows/release.yml` builds the Windows and Linux packages on GitHub's servers.

**Test build (no release):** open the **Actions** tab, select **Build and release UI** and click **Run workflow**. The packages are available under **Artifacts** on the run page.

**Release:**

1. Update `APP_VERSION` in `UI/ATEK_RF_MODULES_USER_INTERFACE.py`, commit and push.
2. Create and push a tag with the same version:

```bash
git tag v2.1.0
git push origin v2.1.0
```

The workflow checks that the tag matches `APP_VERSION`, builds both packages (Linux on Ubuntu 22.04 for wide compatibility) and publishes them as a GitHub Release.

---

## Build Output Directories

The following directories are generated automatically and should not be committed:

```text
UI/build/
UI/dist/
UI/venv/
UI/*.spec
```

The PyInstaller `.spec` file is generated by the build scripts on every build and is not part of the repository.

---

## Development Notes

- `ATEK_RF_MODULES_USER_INTERFACE.py` is the desktop UI entry point.
- All module communication goes through `atek_rf_modules_scpi_api.py`.
- The build scripts expect the UI source file, the API file, `assets.py`, logo, and icon to remain in the same `UI/` directory.
- The Python API uses a background serial reader thread.
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

Copyright © 2026 ATEK MIDAS. For licensing terms, see the License section above.
