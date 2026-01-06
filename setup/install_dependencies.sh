#!/bin/bash
# Install Python dependencies
# Usage: ./setup/install_dependencies.sh

echo "==================================="
echo " Python Dependencies Installer"
echo "==================================="

cd "$(dirname "$0")/.."

# Check Python
if ! command -v python &> /dev/null; then
    echo "[!] Python not found. Please install Python 3.10+"
    exit 1
fi

echo "[*] Python version:"
python --version

# Install dependencies
echo ""
echo "[*] Installing dependencies..."
pip install -r requirements.txt

# Optional: Install ttkbootstrap for modern UI
echo ""
read -p "[?] Install ttkbootstrap for modern dark theme? (y/n): " install_ttk
if [ "$install_ttk" = "y" ]; then
    pip install ttkbootstrap
fi

echo ""
echo "[OK] Installation complete!"
echo ""
echo "Run the app with:"
echo "  python schedule_gui.py    # GUI mode"
echo "  python schedule_parser.py # CLI mode"
