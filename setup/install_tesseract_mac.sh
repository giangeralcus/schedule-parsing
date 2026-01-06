#!/bin/bash
# Install Tesseract OCR on macOS
# Usage: ./setup/install_tesseract_mac.sh

echo "==================================="
echo " Tesseract OCR Installer - macOS"
echo "==================================="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "[!] Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Tesseract
echo "[*] Installing Tesseract OCR..."
brew install tesseract

# Verify installation
if command -v tesseract &> /dev/null; then
    echo ""
    echo "[OK] Tesseract installed successfully!"
    tesseract --version
else
    echo "[!] Installation failed. Please install manually:"
    echo "    brew install tesseract"
fi
