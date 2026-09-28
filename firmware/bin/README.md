# Pre-built Firmware

Ready-to-flash firmware images for the modules with released hardware.
They are built from the sources in this repository (STM32CubeIDE, Debug configuration)
and are also attached to every GitHub Release as `ATEK_RF_MODULES_firmware_v<version>.zip`.

| Module | Intel HEX | Binary | ELF |
|---|---|---|---|
| ATEK1801 | `ATEK1801.hex` | `ATEK1801.bin` | `ATEK1801.elf` |
| ATEK1601 | `ATEK1601.hex` | `ATEK1601.bin` | `ATEK1601.elf` |

- **`.hex`** – recommended for STM32CubeProgrammer (contains the flash address).
- **`.bin`** – raw image for `dfu-util`; must be written to address `0x08000000`.
- **`.elf`** – includes debug information; for STM32CubeProgrammer or debugging with STM32CubeIDE.

Only load the file of the module you have. A firmware built for another module
drives the control pins incorrectly.

## Updating over USB (DFU)

1. Send `SET:UPDATE` to the module (for example from a serial terminal or with
   `dev.enter_dfu()` in the Python API). The module restarts in the STM32 ROM bootloader.
2. Program the firmware:
   - **STM32CubeProgrammer:** select *USB*, connect, open the `.hex` file and click *Download*.
   - **dfu-util:**
     ```bash
     dfu-util -a 0 -s 0x08000000:leave -D ATEK1601.bin
     ```
3. Disconnect and reconnect the USB cable to start the new firmware.

## Updating the images

After building the module in STM32CubeIDE (select the module with `RF_Init(...)` in
`firmware/Core/Src/main.c`), copy the resulting `.elf` here with the module name and
create the `.hex` and `.bin` files, e.g. with the GNU Arm toolchain:

```bash
arm-none-eabi-objcopy -O ihex   ATEK1601.elf ATEK1601.hex
arm-none-eabi-objcopy -O binary ATEK1601.elf ATEK1601.bin
```
