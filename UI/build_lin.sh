#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 ATEK MIDAS
set -e
cd "$(dirname "$0")"

echo "============================================"
echo "  ATEK RF MODULES UI - AUTO BUILD (Linux)"
echo "============================================"
echo

# --- Check Python ---
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found! Install it first:"
    echo "        sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# --- Main python file (fixed name) ---
MAIN_FILE="ATEK_RF_MODULES_USER_INTERFACE.py"

if [ ! -f "$MAIN_FILE" ]; then
    echo "[ERROR] $MAIN_FILE not found in this folder."
    echo "        Place the main file in the same folder as this script."
    exit 1
fi

echo "Main file found : $MAIN_FILE"

# --- Check assets.py ---
if [ ! -f "assets.py" ]; then
    echo
    echo "[WARNING] assets.py not found in this folder!"
    echo "          Logo and PDF datasheets may not load."
    read -p "Press ENTER to continue, or CTRL+C to cancel..."
else
    echo "assets.py found : OK"
fi

# --- Check icon (not embedded on Linux, informational only) ---
if [ -f "ATEK_MIDAS.ico" ]; then
    echo "Icon found      : ATEK_MIDAS.ico (not embedded in Linux binary, used only for Windows build)"
fi

echo
echo "------------------------------------------------"
echo "Preparing virtual environment"
echo "------------------------------------------------"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo
echo "------------------------------------------------"
echo "Checking / installing required packages"
echo "------------------------------------------------"
pip install --upgrade pip >/dev/null
pip install customtkinter pyserial pillow pyinstaller

echo
echo "------------------------------------------------"
echo "Cleaning previous build files"
echo "------------------------------------------------"
rm -rf build dist ./*.spec

echo
echo "------------------------------------------------"
echo "Building  (--onedir --noupx)"
echo "------------------------------------------------"
echo

pyinstaller \
    --name "ATEK_RF_MODULES_UI" \
    --onedir \
    --noupx \
    --clean \
    --noconsole \
    --hidden-import PIL._tkinter_finder \
    "$MAIN_FILE"

# --- Copy license files into the distribution folder ---
cp ../LICENSE ../THIRD_PARTY_NOTICES.md dist/ATEK_RF_MODULES_UI/

deactivate

echo
echo "============================================"
echo "  BUILD COMPLETE!"
echo "  Output folder : dist/ATEK_RF_MODULES_UI/"
echo "  Executable    : dist/ATEK_RF_MODULES_UI/ATEK_RF_MODULES_UI"
echo
echo "  Send the ENTIRE 'dist/ATEK_RF_MODULES_UI' folder"
echo "  to the customer (the binary alone is not enough)."
echo "============================================"
echo
