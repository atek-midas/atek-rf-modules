"""
ATEK RF MODULES USER INTERFACE
Industrial Design | Full OOP Architecture | Thread-Safe Communication | Embedded Assets
"""

import customtkinter as ctk
import serial
import serial.tools.list_ports
import threading
import queue
import time
import os
import sys
import subprocess
import base64
from io import BytesIO
from PIL import Image

# --- Import embedded assets ---
try:
    from assets import ASSETS
except ImportError:
    ASSETS = {}
    print("Warning: assets.py not found. PDFs and Logo will not load.")

# --- Theme and Color Palette ---
ctk.set_appearance_mode("dark")

COLORS = {
    "bg_main": "#0D1117",
    "bg_panel": "#161B22",
    "bg_element": "#21262D",
    "border": "#30363D",
    "accent": "#58A6FF",
    "accent_hover": "#79C0FF",
    "warning": "#D2A8FF",
    "danger": "#F85149",
    "success": "#238636",
    "text_main": "#C9D1D9",
    "text_muted": "#8B949E",
    "led_off": "#101010",
    "led_on": "#39FF14"
}

# --- Module Database & Datasheet Links ---
MODULES = {
    "ATEK357P4": {
        "name": "LF-20 GHz 5-Bit Digital Attenuator",
        "type": "attenuator", "icon": "►", "datasheet": "ATEK357P4.pdf"
    },
    "ATEK1801": {
        "hw_id": "ATEK888P5",
        "name": "20-530 MHz 32-State USB-Controlled Low Pass Filter",
        "type": "tunable_lpf", "icon": "▱", "datasheet": "ATEK888P5.pdf"
    },
    "ATEK950P6": {
        "name": "485-8000 MHz Switchable Filter Bank",
        "type": "filterbank_8", "icon": "≡", "datasheet": "ATEK950P6.pdf"
    },
    "ATEK1601": {
        "hw_id": "ATEK656N5",
        "name": "2-18 GHz Sub-Octave USB-Controlled Filter Bank",
        "type": "filterbank_6", "icon": "≣", "datasheet": "ATEK656N5.pdf"
    },
    "ATEK256N3": {
        "name": "LF-20 GHz Absorptive SPDT Switch",
        "type": "spdt_switch", "icon": "⇌", "datasheet": "ATEK256N3.pdf"
    },
    "ATEK366P5": {
        "name": "2-18 GHz 180° Analog Phase Shifter",
        "type": "phase_shifter", "icon": "≈", "datasheet": "ATEK366P5.pdf"
    }
}

# --- Utility Functions for Embedded Assets ---
def get_image_from_base64(filename, size=(200, 60)):
    b64_str = ASSETS.get(filename, "")
    if not b64_str:
        return None
    try:
        img_data = base64.b64decode(b64_str)
        return ctk.CTkImage(light_image=Image.open(BytesIO(img_data)),
                            dark_image=Image.open(BytesIO(img_data)),
                            size=size)
    except:
        return None

def open_embedded_pdf(filename, log_callback):
    b64_str = ASSETS.get(filename, "")
    if not b64_str:
        log_callback("ERR", f"Datasheet {filename} not found in assets.py", COLORS["danger"])
        return

    temp_path = os.path.join(os.environ.get('TEMP', '/tmp'), filename)
    try:
        if not os.path.exists(temp_path):
            with open(temp_path, "wb") as f:
                f.write(base64.b64decode(b64_str))

        if sys.platform == "win32":
            os.startfile(temp_path)
        elif sys.platform == "darwin":
            subprocess.call(["open", temp_path])
        else:
            subprocess.call(["xdg-open", temp_path])
        log_callback("SYS", f"Datasheet opened: {filename}", COLORS["accent"])
    except Exception as e:
        log_callback("ERR", f"Failed to open PDF: {e}", COLORS["danger"])

# ---------------------------------------------------------
# COMMUNICATION ENGINE (Thread-Safe)
# ---------------------------------------------------------
class SerialEngine:
    def __init__(self, log_callback, rx_callback):
        self.ser = None
        self.tx_queue = queue.Queue()
        self.running = False
        self.log_callback = log_callback
        self.rx_callback = rx_callback

    def connect(self, port, baud):
        if self.ser and self.ser.is_open:
            self.disconnect()
        try:
            self.ser = serial.Serial(port, baudrate=baud, timeout=1)
            self.running = True
            threading.Thread(target=self._io_loop, daemon=True).start()
            self.log_callback("SYS", f"Connected to {port} (@{baud} baud)", COLORS["success"])
            return True
        except Exception as e:
            self.log_callback("ERR", f"Connection Error: {e}", COLORS["danger"])
            return False

    def disconnect(self):
        self.running = False
        time.sleep(0.1)
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.log_callback("SYS", "Disconnected", COLORS["danger"])

    def send(self, data: bytes):
        if self.running:
            self.tx_queue.put(data)

    def _io_loop(self):
        while self.running:
            if not self.tx_queue.empty():
                try:
                    data = self.tx_queue.get()
                    self.ser.write(data)
                    text_str = data.decode('utf-8', errors='ignore').strip()
                    self.log_callback("TX", text_str, COLORS["accent"])
                except Exception as e:
                    self.log_callback("ERR", f"TX Error: {e}", COLORS["danger"])

            if self.ser.in_waiting > 0:
                try:
                    rx_data = self.ser.read(self.ser.in_waiting)
                    self.rx_callback(rx_data)
                except:
                    pass
            time.sleep(0.01)

# ---------------------------------------------------------
# UI COMPONENTS (OOP & DATASHEET LOGIC)
# ---------------------------------------------------------
class BasePanel(ctk.CTkFrame):
    def __init__(self, master, engine, module_id, log_callback, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.engine = engine
        self.module_id = module_id
        self.info = MODULES[module_id]
        self.log_callback = log_callback

        header = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        header.pack(fill="x", pady=(0, 15))

        top_row = ctk.CTkFrame(header, fg_color="transparent")
        top_row.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(top_row, text=f"{self.info['icon']}  {self.module_id}", font=("Courier New", 24, "bold"), text_color=COLORS["accent"]).pack(side="left")
        ctk.CTkButton(top_row, text="📄 Open Datasheet", width=140, fg_color=COLORS["bg_element"], border_width=1, border_color=COLORS["border"], hover_color=COLORS["border"], command=lambda: open_embedded_pdf(self.info["datasheet"], self.log_callback)).pack(side="right")

        ctk.CTkLabel(header, text=self.info["name"], font=("Courier New", 12), text_color=COLORS["text_muted"]).pack(anchor="w", padx=15, pady=(0, 15))

    def create_card(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", pady=5)
        return card

    def next_demo_state(self):
        pass

class AttenuatorPanel(BasePanel):
    def __init__(self, master, engine, module_id, log_callback, **kwargs):
        super().__init__(master, engine, module_id, log_callback, **kwargs)
        self.val = 0
        self.leds = []
        self.build_ui()

    def build_ui(self):
        disp_card = self.create_card()
        self.lbl_val = ctk.CTkLabel(disp_card, text="00", font=("Courier New", 72, "bold"), text_color=COLORS["text_main"])
        self.lbl_val.pack(pady=(20, 0))
        ctk.CTkLabel(disp_card, text="dB", font=("Courier New", 14), text_color=COLORS["text_muted"]).pack(pady=(0, 10))

        led_frame = ctk.CTkFrame(disp_card, fg_color="transparent")
        led_frame.pack(pady=(0, 20))
        for i in range(5):
            lbl = ctk.CTkLabel(led_frame, text=f"P{5 - i}", font=("Courier New", 10))
            lbl.grid(row=0, column=i, padx=8)
            led = ctk.CTkFrame(led_frame, width=15, height=15, corner_radius=8, fg_color=COLORS["led_off"])
            led.grid(row=1, column=i, padx=8, pady=5)
            self.leds.append(led)

        ctrl_card = self.create_card()
        self.slider = ctk.CTkSlider(ctrl_card, from_=0, to=31, number_of_steps=31, button_color=COLORS["accent"], progress_color=COLORS["accent"])
        self.slider.set(0)
        self.slider.pack(fill="x", padx=20, pady=25)
        self.slider.configure(command=self.on_slide)

    def on_slide(self, value):
        self.update_val(int(round(float(value))))

    def update_val(self, new_val):
        self.val = max(0, min(31, new_val))
        self.lbl_val.configure(text=f"{self.val:02d}")
        self.slider.set(self.val)
        self.engine.send(f"SET:{self.val}\n".encode('utf-8'))

        bin_str = f"{self.val:05b}"
        for i, bit in enumerate(bin_str):
            self.leds[i].configure(fg_color=COLORS["led_on"] if bit == '1' else COLORS["led_off"])

    def sync_from_hardware(self, val):
        self.val = max(0, min(31, val))
        self.lbl_val.configure(text=f"{self.val:02d}")
        self.slider.set(self.val)
        bin_str = f"{self.val:05b}"
        for i, bit in enumerate(bin_str):
            self.leds[i].configure(fg_color=COLORS["led_on"] if bit == '1' else COLORS["led_off"])

    def next_demo_state(self):
        next_val = (self.val + 1) if self.val < 31 else 0
        self.update_val(next_val)

class TunableLPFPanel(BasePanel):
    def __init__(self, master, engine, module_id, log_callback, **kwargs):
        super().__init__(master, engine, module_id, log_callback, **kwargs)
        self.frequencies = [
            27, 28, 29, 30, 31, 32, 33, 34, 48, 51, 55, 58, 68, 75, 95, 112,
            150, 155, 160, 164, 168, 172, 176, 180, 230, 245, 265, 285, 310, 350, 425, 530
        ]
        self.build_ui()

    def build_ui(self):
        ctrl_card = self.create_card()
        self.lbl_band = ctk.CTkLabel(ctrl_card, text="Band 1 (27 MHz)", font=("Courier New", 24, "bold"), text_color=COLORS["text_main"])
        self.lbl_band.pack(pady=20)

        self.slider = ctk.CTkSlider(ctrl_card, from_=1, to=32, number_of_steps=31, button_color=COLORS["accent"])
        self.slider.set(1)
        self.slider.pack(fill="x", padx=20, pady=25)
        self.slider.configure(command=self.update_val)

    def update_val(self, value):
        band = int(round(float(value)))
        mhz_exact = self.frequencies[band - 1]
        self.lbl_band.configure(text=f"Band {band} ({mhz_exact} MHz)")
        self.slider.set(band)
        self.engine.send(f"SET:{band - 1}\n".encode('utf-8'))

    def sync_from_hardware(self, val):
        band = val + 1
        mhz_exact = self.frequencies[val]
        self.lbl_band.configure(text=f"Band {band} ({mhz_exact} MHz)")
        self.slider.set(band)

    def next_demo_state(self):
        current = int(self.slider.get())
        next_val = (current + 1) if current < 32 else 1
        self.update_val(next_val)

class FilterBank8Panel(BasePanel):
    def __init__(self, master, engine, module_id, log_callback, **kwargs):
        super().__init__(master, engine, module_id, log_callback, **kwargs)
        self.buttons = []
        self.current_idx = 0
        self.bands = [
            {"name": "Band 1 (485-810 MHz)",   "code": 0x00},
            {"name": "Band 2 (670-1125 MHz)",  "code": 0x06},
            {"name": "Band 3 (960-1670 MHz)",  "code": 0x04},
            {"name": "Band 4 (1440-2560 MHz)", "code": 0x05},
            {"name": "Band 5 (2140-3850 MHz)", "code": 0x02},
            {"name": "Band 6 (3300-5880 MHz)", "code": 0x01},
            {"name": "Band 7 (4820-8500 MHz)", "code": 0x03},
            {"name": "External Bypass",        "code": 0x07}
        ]
        self.build_ui()

    def build_ui(self):
        grid_card = self.create_card()
        grid_card.pack_configure(padx=10, ipadx=10, ipady=10)

        for i, b_data in enumerate(self.bands):
            btn = ctk.CTkButton(grid_card, text=b_data["name"], height=40, fg_color=COLORS["bg_element"], border_width=1, border_color=COLORS["border"], hover_color=COLORS["accent_hover"],
                                command=lambda idx=i: self.set_band(idx))
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=10, sticky="ew")
            self.buttons.append(btn)
            grid_card.columnconfigure(i % 2, weight=1)
        self.set_band(0)

    def set_band(self, idx):
        self.current_idx = idx
        for i, btn in enumerate(self.buttons):
            btn.configure(fg_color=COLORS["accent"] if i == idx else COLORS["bg_element"], text_color=COLORS["bg_main"] if i == idx else COLORS["text_main"])
        self.engine.send(f"SET:{idx}\n".encode('utf-8'))

    def sync_from_hardware(self, val):
        self.current_idx = val
        for i, btn in enumerate(self.buttons):
            btn.configure(fg_color=COLORS["accent"] if i == val else COLORS["bg_element"],
                          text_color=COLORS["bg_main"] if i == val else COLORS["text_main"])

    def next_demo_state(self):
        next_val = (self.current_idx + 1) % 8
        self.set_band(next_val)

class FilterBank6Panel(BasePanel):
    def __init__(self, master, engine, module_id, log_callback, **kwargs):
        super().__init__(master, engine, module_id, log_callback, **kwargs)
        self.buttons = []
        self.current_idx = 0
        self.bands = [
            {"name": "Band 1 (1.9-3.5 GHz)",  "code": 0x07},
            {"name": "Band 2 (2.8-5.4 GHz)",  "code": 0x02},
            {"name": "Band 3 (4.5-9.1 GHz)",  "code": 0x05},
            {"name": "Band 4 (7.1-12.3 GHz)", "code": 0x04},
            {"name": "Band 5 (9.9-15.3 GHz)", "code": 0x06},
            {"name": "Band 6 (12.5-18 GHz)",  "code": 0x03}
        ]
        self.build_ui()

    def build_ui(self):
        grid_card = self.create_card()
        grid_card.pack_configure(padx=10, ipadx=10, ipady=10)

        for i, b_data in enumerate(self.bands):
            btn = ctk.CTkButton(grid_card, text=b_data["name"], height=40, fg_color=COLORS["bg_element"], border_width=1, border_color=COLORS["border"], hover_color=COLORS["accent_hover"],
                                command=lambda idx=i: self.set_band(idx))
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=10, sticky="ew")
            self.buttons.append(btn)
            grid_card.columnconfigure(i % 2, weight=1)
        self.set_band(0)

    def set_band(self, idx):
        self.current_idx = idx
        for i, btn in enumerate(self.buttons):
            btn.configure(fg_color=COLORS["accent"] if i == idx else COLORS["bg_element"], text_color=COLORS["bg_main"] if i == idx else COLORS["text_main"])
        self.engine.send(f"SET:{idx}\n".encode('utf-8'))

    def sync_from_hardware(self, val):
        self.current_idx = val
        for i, btn in enumerate(self.buttons):
            btn.configure(fg_color=COLORS["accent"] if i == val else COLORS["bg_element"],
                          text_color=COLORS["bg_main"] if i == val else COLORS["text_main"])

    def next_demo_state(self):
        next_val = (self.current_idx + 1) % 6
        self.set_band(next_val)

class SPDTSwitchPanel(BasePanel):
    def __init__(self, master, engine, module_id, log_callback, **kwargs):
        super().__init__(master, engine, module_id, log_callback, **kwargs)
        self.btn_rf1 = None
        self.btn_rf2 = None
        self.current_state = 0
        self.build_ui()

    def build_ui(self):
        card = self.create_card()
        card.pack_configure(padx=20, pady=20, ipadx=10, ipady=10)

        self.btn_rf1 = ctk.CTkButton(card, text="RFC ➔ RF1 (ON)", height=60, font=("Courier New", 18, "bold"), command=lambda: self.set_switch(0))
        self.btn_rf1.pack(fill="x", padx=20, pady=10)

        self.btn_rf2 = ctk.CTkButton(card, text="RFC ➔ RF2 (ON)", height=60, font=("Courier New", 18, "bold"), command=lambda: self.set_switch(1))
        self.btn_rf2.pack(fill="x", padx=20, pady=10)
        self.set_switch(0)

    def set_switch(self, state):
        self.current_state = state
        if state == 0:
            self.btn_rf1.configure(fg_color=COLORS["success"], text_color="#FFF")
            self.btn_rf2.configure(fg_color=COLORS["bg_element"], text_color=COLORS["text_muted"])
        else:
            self.btn_rf2.configure(fg_color=COLORS["success"], text_color="#FFF")
            self.btn_rf1.configure(fg_color=COLORS["bg_element"], text_color=COLORS["text_muted"])
        self.engine.send(f"SET:{state}\n".encode('utf-8'))

    def sync_from_hardware(self, val):
        self.current_state = val
        if val == 0:
            self.btn_rf1.configure(fg_color=COLORS["success"], text_color="#FFF")
            self.btn_rf2.configure(fg_color=COLORS["bg_element"], text_color=COLORS["text_muted"])
        else:
            self.btn_rf2.configure(fg_color=COLORS["success"], text_color="#FFF")
            self.btn_rf1.configure(fg_color=COLORS["bg_element"], text_color=COLORS["text_muted"])

    def next_demo_state(self):
        next_val = 1 if self.current_state == 0 else 0
        self.set_switch(next_val)

class PhaseShifterPanel(BasePanel):
    def __init__(self, master, engine, module_id, log_callback, **kwargs):
        super().__init__(master, engine, module_id, log_callback, **kwargs)
        self.current_index = 0
        self.build_ui()

    def build_ui(self):
        ctrl_card = self.create_card()
        self.lbl_val = ctk.CTkLabel(ctrl_card, text="0.0 V", font=("Courier New", 48, "bold"), text_color=COLORS["text_main"])
        self.lbl_val.pack(pady=(20, 0))

        self.lbl_info = ctk.CTkLabel(ctrl_card, text="Calculated DAC Output: 0x00", font=("Courier New", 12), text_color=COLORS["warning"])
        self.lbl_info.pack(pady=(0, 10))

        self.slider = ctk.CTkSlider(self, from_=0, to=100, number_of_steps=100, command=self.update_val)
        self.slider.set(0.0)
        self.slider.pack(fill="x", padx=20, pady=25)

    def update_val(self, value):
        self.current_index = int(round(float(value)))
        voltage = self.current_index * 0.1
        self.lbl_val.configure(text=f"{voltage:.1f} V")

        dac_value = int((voltage / 10.0) * 255)
        self.lbl_info.configure(text=f"Calculated DAC Output: 0x{dac_value:02X}")
        self.engine.send(f"SET:{self.current_index}\n".encode('utf-8'))
        self.slider.set(self.current_index)

    def sync_from_hardware(self, val):
        self.current_index = val
        voltage = val * 0.1
        self.lbl_val.configure(text=f"{voltage:.1f} V")
        dac_value = int((voltage / 10.0) * 255)
        self.lbl_info.configure(text=f"Calculated DAC Output: 0x{dac_value:02X}")
        self.slider.set(val)

    def next_demo_state(self):
        next_val = self.current_index + 10
        if next_val > 100:
            next_val = 0
        self.update_val(next_val)

# ---------------------------------------------------------
# MAIN APPLICATION
# ---------------------------------------------------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ATEK RF MODULES USER INTERFACE")
        self.geometry("950x750")
        self.configure(fg_color=COLORS["bg_main"])

        self.engine = SerialEngine(self.log, self.process_rx)
        self.active_panel = None
        self.rx_buffer = ""

        # YENİ: Demo mod durumunu tutan değişken (Varsayılan olarak Kapalı)
        self.demo_mode_active = ctk.BooleanVar(value=False)

        self.setup_layout()

        # Timer her zaman arka planda döner ama işlem yapıp yapmayacağına değişkene bakarak karar verir
        self.after(2000, self.demo_tick)

    def setup_layout(self):
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=COLORS["bg_panel"], border_width=1, border_color=COLORS["border"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo_img = get_image_from_base64("logo_new-300x86.png", size=(200, 60))
        if logo_img:
            ctk.CTkLabel(self.sidebar, image=logo_img, text="").pack(pady=(25, 10))
        else:
            ctk.CTkLabel(self.sidebar, text="ATEK MIDAS", font=("Arial", 24, "bold"), text_color=COLORS["accent"]).pack(pady=(25, 10))

        # Standart Başlık
        self.lbl_title = ctk.CTkLabel(self.sidebar, text="", font=("Arial", 12, "bold"), text_color=COLORS["text_muted"])
        self.lbl_title.pack(pady=(10, 15))

        # YENİ: Uyarı etiketini oluşturduk ama HİÇ GÖSTERMEDİK (pack yapmadık)
        self.demo_warning_lbl = ctk.CTkLabel(self.sidebar, text="⚠️ DEMO MODE ACTIVE", font=("Arial", 14, "bold"), text_color="#161B22", fg_color=COLORS["warning"], corner_radius=5)

        self.active_module_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.active_module_container.pack(fill="x", padx=10, pady=10)

        self.lbl_no_device = ctk.CTkLabel(self.active_module_container, text="No Device Connected", text_color=COLORS["text_muted"], font=("Arial", 12, "italic"))
        self.lbl_no_device.pack(pady=20)

        # YENİ: Demo Modu Şalteri (Switch) en alta sabitlendi
        self.demo_switch = ctk.CTkSwitch(self.sidebar, text="Demo Mode", font=("Arial", 12),
                                         variable=self.demo_mode_active, command=self.on_demo_toggle,
                                         progress_color=COLORS["warning"], button_color=COLORS["text_main"])
        self.demo_switch.pack(side="bottom", pady=20, padx=20, anchor="w")

        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.pack(side="right", fill="both", expand=True)

        self.content_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.footer = ctk.CTkFrame(self.main_area, height=150, corner_radius=0, fg_color=COLORS["bg_panel"], border_width=1, border_color=COLORS["border"])
        self.footer.pack(side="bottom", fill="x")
        self.footer.pack_propagate(False)

        conn_frame = ctk.CTkFrame(self.footer, fg_color="transparent")
        conn_frame.pack(side="left", fill="y", padx=10, pady=10)

        port_row = ctk.CTkFrame(conn_frame, fg_color="transparent")
        port_row.pack(pady=2)

        self.combo_port = ctk.CTkComboBox(port_row, values=["Loading..."], width=90)
        self.combo_port.pack(side="left", padx=(0, 5))

        self.btn_refresh = ctk.CTkButton(port_row, text="⟳", width=25, fg_color=COLORS["bg_element"], border_width=1, border_color=COLORS["border"], hover_color=COLORS["border"], command=self.refresh_ports)
        self.btn_refresh.pack(side="left")

        self.combo_baud = ctk.CTkComboBox(conn_frame, values=["9600", "115200"], width=120)
        self.combo_baud.set("115200")
        self.combo_baud.pack(pady=5)

        self.btn_conn = ctk.CTkButton(conn_frame, text="CONNECT", width=120, fg_color=COLORS["success"], hover_color="#1e6e2b", command=self.toggle_conn)
        self.btn_conn.pack(pady=5)

        self.log_box = ctk.CTkTextbox(self.footer, fg_color=COLORS["bg_main"], text_color=COLORS["text_muted"], font=("Courier New", 12))
        self.log_box.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)
        self.log_box.insert("end", "System Initialized. Awaiting Hardware Connection...\n")

        self.refresh_ports()

    # YENİ: Demo modunu şalterden değiştirdiğimizde çalışacak fonksiyon
    def on_demo_toggle(self):
        if self.demo_mode_active.get():
            # Demo açık ise başlığın üstüne sarı uyarıyı koy
            self.lbl_title.pack_forget()
            self.demo_warning_lbl.pack(pady=(10, 15), padx=20, fill="x", before=self.active_module_container)
            self.log("SYS", "Demo Mode ENABLED. Auto-cycling started.", COLORS["warning"])
        else:
            # Demo kapalı ise sarı uyarıyı kaldır, normal başlığı geri getir
            self.demo_warning_lbl.pack_forget()
            self.lbl_title.pack(pady=(10, 15), before=self.active_module_container)
            self.log("SYS", "Demo Mode DISABLED. Manual control restored.", COLORS["accent"])

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports:
            ports = ["No COM"]
        self.combo_port.configure(values=ports)
        self.combo_port.set(ports[0])
        self.log("SYS", "COM ports refreshed.", COLORS["accent"])

    def set_identified_module(self, identified_id):
        for widget in self.active_module_container.winfo_children():
            widget.destroy()

        info = MODULES.get(identified_id)
        if info:
            ctk.CTkLabel(self.active_module_container, text=f"CONNECTED:", font=("Arial", 10, "bold"), text_color=COLORS["text_muted"]).pack(anchor="w", padx=10)
            btn = ctk.CTkButton(self.active_module_container, text=f"{info['icon']}  {identified_id}  ●", anchor="w",
                                fg_color="transparent", text_color=COLORS["success"],
                                hover_color=COLORS["bg_element"], state="normal")
            btn.pack(fill="x", padx=10, pady=5)

        self.select_module(identified_id)
        self.after(200, lambda: self.engine.send(b"GET?\r\n"))

    def clear_identified_module(self):
        if self.active_panel:
            self.active_panel.destroy()
            self.active_panel = None

        for widget in self.active_module_container.winfo_children():
            widget.destroy()

        self.lbl_no_device = ctk.CTkLabel(self.active_module_container, text="No Device Connected", text_color=COLORS["text_muted"], font=("Arial", 12, "italic"))
        self.lbl_no_device.pack(pady=20)

    def process_rx(self, rx_data):
        text = rx_data.decode('utf-8', errors='ignore')
        self.rx_buffer += text

        if len(self.rx_buffer) > 500:
            self.rx_buffer = self.rx_buffer[-500:]

        while '\n' in self.rx_buffer or '\r' in self.rx_buffer:
            if '\n' in self.rx_buffer:
                line, self.rx_buffer = self.rx_buffer.split('\n', 1)
            else:
                line, self.rx_buffer = self.rx_buffer.split('\r', 1)

            line = line.strip()
            if not line: continue

            self.log("RX", line, COLORS["warning"])

            for m_id, m_info in MODULES.items():
                expected_id = m_info.get("hw_id", m_id)

                if expected_id in line:
                    self.after(0, lambda m=m_id: self.set_identified_module(m))
                    self.log("SYS", f"Device Identified via IDN: {expected_id} (Loaded as {m_id})", COLORS["success"])
                    break

            if line.startswith("STATE:"):
                try:
                    state_val = int(line.split(":")[1])
                    if self.active_panel:
                        self.after(0, lambda v=state_val: self.active_panel.sync_from_hardware(v))
                except Exception as e:
                    self.log("ERR", f"State Parse Error: {e}", COLORS["danger"])

    def select_module(self, module_id):
        if self.active_panel:
            self.active_panel.destroy()

        m_type = MODULES[module_id]["type"]
        if m_type == "attenuator":
            self.active_panel = AttenuatorPanel(self.content_frame, self.engine, module_id, self.log)
        elif m_type == "tunable_lpf":
            self.active_panel = TunableLPFPanel(self.content_frame, self.engine, module_id, self.log)
        elif m_type == "filterbank_8":
            self.active_panel = FilterBank8Panel(self.content_frame, self.engine, module_id, self.log)
        elif m_type == "filterbank_6":
            self.active_panel = FilterBank6Panel(self.content_frame, self.engine, module_id, self.log)
        elif m_type == "spdt_switch":
            self.active_panel = SPDTSwitchPanel(self.content_frame, self.engine, module_id, self.log)
        elif m_type == "phase_shifter":
            self.active_panel = PhaseShifterPanel(self.content_frame, self.engine, module_id, self.log)

        self.active_panel.pack(fill="both", expand=True)
        self.log("SYS", f"Module Loaded: {module_id}", COLORS["accent"])

    def toggle_conn(self):
        if not self.engine.running:
            port = self.combo_port.get()

            if port in ["No COM", "Loading...", ""]:
                self.log("ERR", "Please select a valid COM port!", COLORS["danger"])
                return

            baud = int(self.combo_baud.get())
            if self.engine.connect(port, baud):
                self.btn_conn.configure(text="DISCONNECT", fg_color=COLORS["danger"], hover_color="#c93832")
                self.after(200, lambda: self.engine.send(b"*IDN?\r\n"))
        else:
            self.engine.disconnect()
            self.btn_conn.configure(text="CONNECT", fg_color=COLORS["success"], hover_color="#1e6e2b")
            self.clear_identified_module()
            self.rx_buffer = ""

    def log(self, prefix, msg, color):
        def update():
            timestamp = time.strftime("%H:%M:%S")
            log_text = f"[{timestamp}] {prefix} | {msg}\n"
            tag_name = f"color_{color}"
            self.log_box.tag_config(tag_name, foreground=color)
            self.log_box.insert("end", log_text, tag_name)
            self.log_box.see("end")
        self.after(0, update)

    # YENİ: Timer her zaman çalışır ama şalter açıksa panel değişimini tetikler
    def demo_tick(self):
        if self.demo_mode_active.get() and self.engine.running and self.active_panel:
            self.active_panel.next_demo_state()

        self.after(2000, self.demo_tick)

if __name__ == "__main__":
    app = App()
    app.mainloop()