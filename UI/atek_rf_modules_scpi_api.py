"""
ATEK RF Modules SCPI API
========================

Python API for USB-controlled ATEK MIDAS RF modules.

The modules enumerate as a USB CDC virtual COM port and accept a small,
SCPI-like text protocol (*IDN?, GET?, SET:<n>, SET:UPDATE). This file wraps
that protocol in a thread-safe, object-oriented API so that applications can
control the modules without dealing with raw serial traffic.

Requirements : Python 3.8+ and pyserial  (pip install pyserial)
Installation : copy this file next to your script and `import` it.

Quick start
-----------
    import atek_rf_modules_scpi_api as atek

    with atek.connect("COM5") as dev:          # "/dev/ttyACM0" on Linux
        print(dev.model)                        # e.g. "ATEK950P6"
        dev.set_state(3)                        # generic, works for every module
        print(dev.get_state())

Copyright (c) ATEK MIDAS. All rights reserved.
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import serial
import serial.tools.list_ports

__version__ = "1.0.0"

__all__ = [
    "__version__",
    # Errors
    "AtekError", "AtekConnectionError", "AtekTimeoutError", "AtekStateError",
    # Data
    "ModuleInfo", "DeviceInfo", "MODULES",
    # Device classes
    "AtekRFModule", "Attenuator", "TunableLowPassFilter", "FilterBank",
    "ATEK950P6", "ATEK1601", "SPDTSwitch", "PhaseShifter",
    # Functions
    "connect", "find_devices", "list_serial_ports",
]

DEFAULT_TIMEOUT = 1.0          # [s] maximum wait for a query response
DEFAULT_BAUDRATE = 115200      # Ignored by USB CDC, kept for pyserial compatibility
SET_CONFIRM_TIMEOUT = 0.3      # [s] wait for STATE:<n> after SET before falling back to GET?
STATE_PREFIX = "STATE:"
MAX_COMMAND_LENGTH = 63        # Firmware receive buffer limit (characters)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class AtekError(Exception):
    """Base class for all errors raised by this API."""


class AtekConnectionError(AtekError):
    """The serial port could not be opened or the connection was lost."""


class AtekTimeoutError(AtekError):
    """The module did not answer within the timeout."""


class AtekStateError(AtekError):
    """Invalid state requested, or the module did not apply the state."""


# ---------------------------------------------------------------------------
# Module database
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ModuleInfo:
    """Static information about a module type."""
    model: str          # Module name, as returned by *IDN?
    chip: str           # RF chip used inside the module (datasheet name)
    description: str
    kind: str           # attenuator | tunable_lpf | filter_bank | spdt_switch | phase_shifter
    num_states: int     # Valid states are 0 ... num_states - 1
    available: bool = True

    @property
    def max_state(self) -> int:
        return self.num_states - 1


MODULES: Dict[str, ModuleInfo] = {
    "ATEK357P4": ModuleInfo("ATEK357P4", "ATEK357P4", "LF-20 GHz 5-Bit Digital Attenuator", "attenuator", 32),
    "ATEK1801":  ModuleInfo("ATEK1801", "ATEK888P5", "20-550 MHz 32-State USB-Controlled Low Pass Filter", "tunable_lpf", 32),
    "ATEK950P6": ModuleInfo("ATEK950P6", "ATEK950P6", "485-8500 MHz Switchable Filter Bank", "filter_bank", 8),
    "ATEK1601":  ModuleInfo("ATEK1601", "ATEK656N5", "2-18 GHz Sub-Octave USB-Controlled Filter Bank", "filter_bank", 6),
    "ATEK256N3": ModuleInfo("ATEK256N3", "ATEK256N3", "LF-20 GHz Absorptive SPDT Switch", "spdt_switch", 2),
    "ATEK366P5": ModuleInfo("ATEK366P5", "ATEK366P5", "2-18 GHz 180 deg Analog Phase Shifter", "phase_shifter", 101,
                            available=False),
}


@dataclass(frozen=True)
class DeviceInfo:
    """Result entry of find_devices()."""
    port: str
    model: str
    description: str


# ---------------------------------------------------------------------------
# Base device class
# ---------------------------------------------------------------------------
class AtekRFModule:
    """
    Generic ATEK RF module. Works with every module through state indexes.

    Normally created through connect(), which returns the matching subclass
    (Attenuator, FilterBank, ...) with additional module-specific methods.

    Callbacks (optional, all called from the background reader thread):
        on_state_change(state: int)   every STATE:<n> message, including changes
                                      made with the front-panel buttons
        on_tx(line: str)              every line sent to the module
        on_rx(line: str)              every line received from the module
        on_disconnect(error: Exception)  connection lost unexpectedly
    """

    def __init__(self, port: str, *, timeout: float = DEFAULT_TIMEOUT,
                 baudrate: int = DEFAULT_BAUDRATE, open_port: bool = True,
                 identify: bool = True,
                 on_state_change: Optional[Callable[[int], None]] = None,
                 on_tx: Optional[Callable[[str], None]] = None,
                 on_rx: Optional[Callable[[str], None]] = None,
                 on_disconnect: Optional[Callable[[Exception], None]] = None):
        self.port = port
        self.timeout = timeout
        self.baudrate = baudrate

        self.on_state_change = on_state_change
        self.on_tx = on_tx
        self.on_rx = on_rx
        self.on_disconnect = on_disconnect

        self._ser: Optional[serial.Serial] = None
        self._reader: Optional[threading.Thread] = None
        self._running = False
        self._rx_queue: "queue.Queue[str]" = queue.Queue()
        self._txn_lock = threading.RLock()     # One request/response exchange at a time
        self._write_lock = threading.Lock()
        self._model: Optional[str] = None
        self._state: Optional[int] = None

        if open_port:
            self.open()
            if identify:
                try:
                    self.identify()
                except Exception:
                    self.close()
                    raise

    # --- Properties ------------------------------------------------------
    @property
    def model(self) -> Optional[str]:
        """Module name returned by *IDN? (None before identify())."""
        return self._model

    @property
    def info(self) -> Optional[ModuleInfo]:
        """Static ModuleInfo of the connected module."""
        return MODULES.get(self._model) if self._model else None

    @property
    def num_states(self) -> Optional[int]:
        return self.info.num_states if self.info else None

    @property
    def last_state(self) -> Optional[int]:
        """Last state reported by the module (no communication)."""
        return self._state

    @property
    def is_open(self) -> bool:
        return self._running and self._ser is not None and self._ser.is_open

    # --- Connection ------------------------------------------------------
    def open(self) -> None:
        """Open the serial port and start the background reader."""
        if self.is_open:
            return
        try:
            self._ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=0.05)
        except serial.SerialException as e:
            raise AtekConnectionError(f"Cannot open {self.port}: {e}") from e
        try:
            self._ser.reset_input_buffer()
        except serial.SerialException:
            pass
        self._running = True
        self._reader = threading.Thread(target=self._reader_loop, name=f"atek-rx-{self.port}", daemon=True)
        self._reader.start()

    def close(self) -> None:
        """Stop the reader and close the serial port."""
        self._running = False
        if self._reader is not None and self._reader is not threading.current_thread():
            self._reader.join(timeout=0.5)
        self._reader = None
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser = None

    def __enter__(self) -> "AtekRFModule":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __repr__(self) -> str:
        status = "open" if self.is_open else "closed"
        return f"<{type(self).__name__} {self._model or '?'} on {self.port} ({status})>"

    # --- Raw protocol ----------------------------------------------------
    def write(self, command: str) -> None:
        """Send a raw command line (terminator added automatically)."""
        command = command.strip()
        if not command:
            raise ValueError("Empty command")
        if len(command) > MAX_COMMAND_LENGTH:
            raise ValueError(f"Command longer than {MAX_COMMAND_LENGTH} characters")
        if not self.is_open:
            raise AtekConnectionError("Port is not open")
        try:
            with self._write_lock:
                self._ser.write((command + "\r\n").encode("ascii"))
        except (serial.SerialException, OSError, TypeError, AttributeError) as e:
            # TypeError/AttributeError: port closed concurrently by the reader thread
            self._handle_connection_lost(e)
            raise AtekConnectionError(f"Write failed: {e}") from e
        self._fire(self.on_tx, command)

    def query(self, command: str, timeout: Optional[float] = None,
              accept: Optional[Callable[[str], bool]] = None) -> str:
        """
        Send a command and return the first response line.
        `accept` can filter lines, e.g. to skip unsolicited STATE messages.
        """
        with self._txn_lock:
            self._drain()
            self.write(command)
            return self._wait_line(accept, self.timeout if timeout is None else timeout, command)

    # --- Common commands -------------------------------------------------
    def identify(self) -> str:
        """Send *IDN? and return (and store) the module name."""
        resp = self.query("*IDN?", accept=lambda line: not line.startswith(STATE_PREFIX))
        self._model = resp.strip()
        if self._model not in MODULES:
            raise AtekError(f"Unknown module ID '{self._model}' on {self.port}")
        return self._model

    def get_state(self) -> int:
        """Send GET? and return the current state index."""
        resp = self.query("GET?", accept=lambda line: line.startswith(STATE_PREFIX))
        return self._parse_state(resp)

    def set_state(self, state: int, verify: bool = True) -> int:
        """
        Select a state index (0 ... num_states - 1).

        verify=True : wait for the STATE:<n> confirmation (falls back to GET?)
                      and raise AtekStateError if the module did not apply it.
        verify=False: send and return immediately (e.g. for GUI sliders).
        """
        state = self._validate_state(state)
        if not verify:
            self.write(f"SET:{state}")
            return state

        with self._txn_lock:
            self._drain()
            self.write(f"SET:{state}")
            try:
                resp = self._wait_line(lambda line: line == f"{STATE_PREFIX}{state}",
                                       min(self.timeout, SET_CONFIRM_TIMEOUT), f"SET:{state}")
                return self._parse_state(resp)
            except AtekTimeoutError:
                actual = self.get_state()   # Confirmation lost: check explicitly
                if actual != state:
                    raise AtekStateError(f"Module reports state {actual}, expected {state}")
                return actual

    def enter_dfu(self) -> None:
        """
        Send SET:UPDATE. The module jumps to the STM32 ROM bootloader (USB DFU),
        the virtual COM port disappears and this object is closed.
        Firmware can then be programmed over USB (e.g. STM32CubeProgrammer).
        """
        with self._txn_lock:
            self._drain()
            self.write("SET:UPDATE")
            try:
                self._wait_line(lambda line: "DFU" in line.upper(), 0.5, "SET:UPDATE")
            except AtekError:
                pass    # The port may vanish before the message arrives
        self.close()

    # --- Internals -------------------------------------------------------
    def _validate_state(self, state) -> int:
        if isinstance(state, bool) or not isinstance(state, int):
            raise AtekStateError(f"State must be an integer, got {state!r}")
        n = self.num_states
        if n is not None and not (0 <= state < n):
            raise AtekStateError(f"State {state} out of range 0...{n - 1} for {self._model}")
        return state

    def _parse_state(self, line: str) -> int:
        try:
            return int(line[len(STATE_PREFIX):])
        except ValueError:
            raise AtekError(f"Malformed state response: {line!r}")

    def _drain(self) -> None:
        while True:
            try:
                self._rx_queue.get_nowait()
            except queue.Empty:
                return

    def _wait_line(self, accept, timeout: float, command: str) -> str:
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AtekTimeoutError(f"No response to '{command}' within {timeout:.2f} s")
            if not self.is_open:
                raise AtekConnectionError("Connection closed")
            try:
                line = self._rx_queue.get(timeout=min(remaining, 0.05))
            except queue.Empty:
                continue
            if accept is None or accept(line):
                return line

    def _reader_loop(self) -> None:
        buffer = ""
        while self._running:
            try:
                data = self._ser.read(self._ser.in_waiting or 1)
            except Exception as e:      # Cable pulled, device reset, ...
                if self._running:
                    self._handle_connection_lost(e)
                return
            if not data:
                continue
            buffer += data.decode("ascii", errors="ignore")
            if len(buffer) > 1024:      # Protect against garbage without line ends
                buffer = buffer[-1024:]
            while True:
                idx = min((i for i in (buffer.find("\n"), buffer.find("\r")) if i >= 0), default=-1)
                if idx < 0:
                    break
                line, buffer = buffer[:idx].strip(), buffer[idx + 1:]
                if line:
                    self._handle_line(line)

    def _handle_line(self, line: str) -> None:
        self._fire(self.on_rx, line)
        if line.startswith(STATE_PREFIX):
            try:
                self._state = self._parse_state(line)
                self._fire(self.on_state_change, self._state)
            except AtekError:
                pass
        self._rx_queue.put(line)

    def _handle_connection_lost(self, error: Exception) -> None:
        was_running = self._running
        self._running = False
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
        if was_running:
            self._fire(self.on_disconnect, error)

    @staticmethod
    def _fire(callback, *args) -> None:
        if callback is None:
            return
        try:
            callback(*args)
        except Exception:
            pass    # A faulty user callback must never stop the reader thread


# ---------------------------------------------------------------------------
# Module-specific classes
# ---------------------------------------------------------------------------
class Attenuator(AtekRFModule):
    """ATEK357P4 - 5-bit digital attenuator, 0...31 dB in 1 dB steps (state = dB)."""
    STEP_DB = 1
    MAX_DB = 31

    def set_attenuation(self, db: int, verify: bool = True) -> int:
        """Set attenuation in dB (integer 0...31). Returns the applied value."""
        if isinstance(db, float) and db.is_integer():
            db = int(db)
        if isinstance(db, bool) or not isinstance(db, int) or not (0 <= db <= self.MAX_DB):
            raise AtekStateError(f"Attenuation must be an integer 0...{self.MAX_DB} dB, got {db!r}")
        return self.set_state(db // self.STEP_DB, verify) * self.STEP_DB

    def get_attenuation(self) -> int:
        """Read the attenuation in dB."""
        return self.get_state() * self.STEP_DB


class TunableLowPassFilter(AtekRFModule):
    """ATEK1801 (chip ATEK888P5) - 32-band low pass filter. Band 1...32 = state 0...31."""
    CUTOFFS_MHZ: Tuple[int, ...] = (
        27, 28, 29, 30, 31, 32, 33, 34, 48, 51, 55, 58, 68, 75, 95, 112,
        150, 155, 160, 164, 168, 172, 176, 180, 230, 245, 265, 285, 310, 350, 425, 550,
    )

    def set_band(self, band: int, verify: bool = True) -> int:
        """Select band 1...32."""
        self._check_band(band)
        return self.set_state(band - 1, verify) + 1

    def get_band(self) -> int:
        return self.get_state() + 1

    def get_cutoff_mhz(self) -> int:
        """Nominal cut-off frequency of the active band in MHz."""
        return self.CUTOFFS_MHZ[self.get_state()]

    def set_cutoff_mhz(self, mhz: float, verify: bool = True) -> int:
        """
        Select the lowest band whose nominal cut-off is >= mhz
        (i.e. the tightest filter that still passes `mhz`).
        Returns the selected cut-off in MHz.
        """
        for state, fc in enumerate(self.CUTOFFS_MHZ):
            if fc >= mhz:
                self.set_state(state, verify)
                return fc
        raise AtekStateError(f"{mhz} MHz is above the highest cut-off ({self.CUTOFFS_MHZ[-1]} MHz)")

    def _check_band(self, band) -> None:
        if isinstance(band, bool) or not isinstance(band, int) or not (1 <= band <= len(self.CUTOFFS_MHZ)):
            raise AtekStateError(f"Band must be 1...{len(self.CUTOFFS_MHZ)}, got {band!r}")


class FilterBank(AtekRFModule):
    """Common switchable filter bank logic. Band n (1-based) = state n - 1."""
    BANDS_MHZ: Tuple[Tuple[float, float], ...] = ()
    BYPASS_STATE: Optional[int] = None

    @property
    def num_bands(self) -> int:
        return len(self.BANDS_MHZ)

    def set_band(self, band: int, verify: bool = True) -> int:
        """Select filter band 1...num_bands."""
        if isinstance(band, bool) or not isinstance(band, int) or not (1 <= band <= self.num_bands):
            raise AtekStateError(f"Band must be 1...{self.num_bands}, got {band!r}")
        return self.set_state(band - 1, verify) + 1

    def get_band(self) -> Optional[int]:
        """Active band 1...num_bands, or None when in bypass."""
        state = self.get_state()
        return None if state == self.BYPASS_STATE else state + 1

    def get_band_range_mhz(self, band: Optional[int] = None) -> Tuple[float, float]:
        """(low, high) pass band in MHz of `band` (default: active band)."""
        if band is None:
            band = self.get_band()
            if band is None:
                raise AtekStateError("Module is in bypass")
        if not (1 <= band <= self.num_bands):
            raise AtekStateError(f"Band must be 1...{self.num_bands}, got {band!r}")
        return self.BANDS_MHZ[band - 1]

    def set_frequency_mhz(self, mhz: float, verify: bool = True) -> int:
        """
        Select the band that best covers `mhz` (the band containing the
        frequency closest to its centre). Returns the selected band number.
        """
        candidates = [(abs(mhz - (lo + hi) / 2) / (hi - lo), i + 1)
                      for i, (lo, hi) in enumerate(self.BANDS_MHZ) if lo <= mhz <= hi]
        if not candidates:
            raise AtekStateError(f"{mhz} MHz is not covered by any band")
        return self.set_band(min(candidates)[1], verify)

    def set_bypass(self, verify: bool = True) -> None:
        if self.BYPASS_STATE is None:
            raise AtekStateError(f"{self._model} has no bypass path")
        self.set_state(self.BYPASS_STATE, verify)

    def is_bypass(self) -> bool:
        return self.BYPASS_STATE is not None and self.get_state() == self.BYPASS_STATE


class ATEK950P6(FilterBank):
    """ATEK950P6 - 7-band filter bank (485...8500 MHz) with bypass (state 7)."""
    BANDS_MHZ = ((485, 810), (670, 1125), (960, 1670), (1440, 2560),
                 (2140, 3850), (3300, 5880), (4820, 8500))
    BYPASS_STATE = 7


class ATEK1601(FilterBank):
    """ATEK1601 (chip ATEK656N5) - 6-band sub-octave filter bank, 1.9...18 GHz."""
    BANDS_MHZ = ((1900, 3500), (2800, 5400), (4500, 9100),
                 (7100, 12300), (9900, 15300), (12500, 18000))


class SPDTSwitch(AtekRFModule):
    """ATEK256N3 - SPDT switch. RF1 = state 0, RF2 = state 1."""

    def select(self, rf_port: int, verify: bool = True) -> int:
        """Connect RFC to RF1 (rf_port=1) or RF2 (rf_port=2)."""
        if rf_port not in (1, 2):
            raise AtekStateError(f"rf_port must be 1 or 2, got {rf_port!r}")
        return self.set_state(rf_port - 1, verify) + 1

    def get_selected(self) -> int:
        """Return the RF port (1 or 2) connected to RFC."""
        return self.get_state() + 1


class PhaseShifter(AtekRFModule):
    """ATEK366P5 - reserved. Not yet supported by the module firmware."""


_MODEL_CLASSES = {
    "ATEK357P4": Attenuator,
    "ATEK1801": TunableLowPassFilter,
    "ATEK950P6": ATEK950P6,
    "ATEK1601": ATEK1601,
    "ATEK256N3": SPDTSwitch,
    "ATEK366P5": PhaseShifter,
}


# ---------------------------------------------------------------------------
# Public helper functions
# ---------------------------------------------------------------------------
def connect(port: str, **kwargs) -> AtekRFModule:
    """
    Open `port`, identify the module and return the matching class instance
    (Attenuator, TunableLowPassFilter, ATEK950P6, ATEK1601, SPDTSwitch, ...).
    Keyword arguments are passed to AtekRFModule (timeout, callbacks, ...).
    """
    kwargs["open_port"] = True
    kwargs["identify"] = True
    dev = AtekRFModule(port, **kwargs)
    dev.__class__ = _MODEL_CLASSES.get(dev.model, AtekRFModule)
    return dev


def list_serial_ports() -> List[str]:
    """All serial ports on this computer."""
    return [p.device for p in serial.tools.list_ports.comports()]


def find_devices(ports: Optional[Sequence[str]] = None, timeout: float = 0.5) -> List[DeviceInfo]:
    """
    Probe serial ports with *IDN? and return the ATEK modules found.
    Note: every probed port receives '*IDN?'. Pass `ports` to limit the scan
    if other serial instruments are connected.
    """
    found: List[DeviceInfo] = []
    for port in (ports if ports is not None else list_serial_ports()):
        try:
            with AtekRFModule(port, timeout=timeout) as dev:
                found.append(DeviceInfo(port, dev.model, dev.info.description))
        except (AtekError, ValueError, OSError):
            continue
    return found