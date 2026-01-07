"""
SCHEDULE PARSER GUI v3.0 - Modern Edition
==========================================
Drag & drop interface for parsing shipping schedules
Modern dark theme with ttkbootstrap
"""

import os
import sys
import threading
import tkinter as tk

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try ttkbootstrap first, fallback to ttk
# Note: ttkbootstrap has issues with Python 3.14, force fallback
if sys.version_info >= (3, 14):
    from tkinter import ttk as ttkb
    HAS_BOOTSTRAP = False
else:
    try:
        import ttkbootstrap as ttkb
        from ttkbootstrap.constants import *
        HAS_BOOTSTRAP = True
    except ImportError:
        from tkinter import ttk as ttkb
        HAS_BOOTSTRAP = False

# Try drag-and-drop support
HAS_DND = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    pass

# Try PIL for image preview
HAS_PIL = False
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    pass

from core.config import SCREENSHOTS_DIR, OUTPUT_DIR, CARRIER_MAP
from core.parsers import parse_schedules, get_carrier_from_filename, detect_carrier
from core.models import Schedule
from processors.ocr import OCRProcessor
from formatters.output import format_table, format_email, save_output, copy_to_clipboard


class ScheduleParserGUI:
    def __init__(self):
        # Create main window with DnD support if available
        if HAS_DND:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title("Schedule Parser v3.0")
        self.root.geometry("800x650")
        self.root.minsize(700, 550)

        # Apply theme
        if HAS_BOOTSTRAP:
            self.style = ttkb.Style(theme="darkly")
        else:
            self.root.configure(bg='#2b3e50')

        # Current data
        self.current_file = None
        self.current_schedules = []
        self.current_carrier = None
        self.image_reference = None
        self.ocr = OCRProcessor()

        # Build UI
        self.create_widgets()

        # Setup drag and drop
        if HAS_DND:
            self.setup_dnd()

    def create_widgets(self):
        """Create all UI widgets"""
        # Main container
        main = ttkb.Frame(self.root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # Header
        self.create_header(main)

        # Drop zone + Preview
        self.create_drop_zone(main)

        # Carrier selection
        self.create_carrier_bar(main)

        # Results area
        self.create_results_area(main)

        # Action buttons
        self.create_action_buttons(main)

        # Status bar
        self.create_status_bar(main)

    def create_header(self, parent):
        """Create header with title"""
        header_frame = ttkb.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        if HAS_BOOTSTRAP:
            title = ttkb.Label(
                header_frame,
                text="📦 Schedule Parser",
                font=("Segoe UI", 18, "bold"),
                bootstyle="inverse-primary"
            )
        else:
            title = ttkb.Label(
                header_frame,
                text="Schedule Parser",
                font=("Segoe UI", 18, "bold")
            )
        title.pack(side=tk.LEFT)

        # Right side info
        right_frame = ttkb.Frame(header_frame)
        right_frame.pack(side=tk.RIGHT)

        version = ttkb.Label(
            right_frame,
            text="v3.0 Offline",
            font=("Segoe UI", 10)
        )
        version.pack(anchor='e')

        author = ttkb.Label(
            right_frame,
            text="Made by Gian Geralcus © 2026",
            font=("Segoe UI", 8)
        )
        author.pack(anchor='e')

    def create_drop_zone(self, parent):
        """Create drag & drop zone with optional image preview"""
        if HAS_BOOTSTRAP:
            drop_frame = ttkb.LabelFrame(
                parent,
                text="📁 Drop Screenshot Here",
                bootstyle="info"
            )
        else:
            drop_frame = ttkb.LabelFrame(parent, text="Drop Screenshot Here")
        drop_frame.pack(fill=tk.X, pady=10)

        # Inner frame for content with padding
        inner = ttkb.Frame(drop_frame, padding=10)
        inner.pack(fill=tk.BOTH, expand=True)

        # Canvas for drop zone / image preview
        self.drop_canvas = tk.Canvas(
            inner,
            height=120,
            bg='#3d5a73' if HAS_BOOTSTRAP else '#e0e0e0',
            highlightthickness=2,
            highlightbackground='#4a90a4'
        )
        self.drop_canvas.pack(fill=tk.X, pady=5)

        # Default text
        self.drop_text_id = self.drop_canvas.create_text(
            400, 60,
            text="🖼️  Drag & Drop Screenshot Here\nor click Browse button below",
            font=("Segoe UI", 12),
            fill='#a0b0c0' if HAS_BOOTSTRAP else '#666666',
            justify='center'
        )

        # Browse button
        btn_frame = ttkb.Frame(drop_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        if HAS_BOOTSTRAP:
            self.browse_btn = ttkb.Button(
                btn_frame,
                text="📂 Browse File",
                command=self.browse_file,
                bootstyle="info-outline",
                width=15
            )
        else:
            self.browse_btn = ttkb.Button(
                btn_frame,
                text="Browse File",
                command=self.browse_file,
                width=15
            )
        self.browse_btn.pack(side=tk.LEFT, padx=5)

        # File info label
        self.file_label = ttkb.Label(
            btn_frame,
            text="No file selected",
            font=("Segoe UI", 9)
        )
        self.file_label.pack(side=tk.LEFT, padx=15)

        # Store reference for DnD
        self.drop_frame = drop_frame

    def create_carrier_bar(self, parent):
        """Create carrier selection bar"""
        carrier_frame = ttkb.Frame(parent)
        carrier_frame.pack(fill=tk.X, pady=5)

        ttkb.Label(carrier_frame, text="Carrier:", font=("Segoe UI", 10)).pack(side=tk.LEFT)

        self.carrier_var = tk.StringVar(value="Auto-detect")
        carriers = ["Auto-detect"] + sorted(set(CARRIER_MAP.values()))

        if HAS_BOOTSTRAP:
            self.carrier_combo = ttkb.Combobox(
                carrier_frame,
                textvariable=self.carrier_var,
                values=carriers,
                state='readonly',
                bootstyle="primary",
                width=18,
                font=("Segoe UI", 10)
            )
        else:
            self.carrier_combo = ttkb.Combobox(
                carrier_frame,
                textvariable=self.carrier_var,
                values=carriers,
                state='readonly',
                width=18
            )
        self.carrier_combo.pack(side=tk.LEFT, padx=10)

        # Process button
        if HAS_BOOTSTRAP:
            self.process_btn = ttkb.Button(
                carrier_frame,
                text="⚡ Process",
                command=self.process_current_file,
                bootstyle="success",
                width=12,
                state='disabled'
            )
        else:
            self.process_btn = ttkb.Button(
                carrier_frame,
                text="Process",
                command=self.process_current_file,
                width=12,
                state='disabled'
            )
        self.process_btn.pack(side=tk.LEFT, padx=5)

    def create_results_area(self, parent):
        """Create scrollable results display"""
        if HAS_BOOTSTRAP:
            result_frame = ttkb.LabelFrame(
                parent,
                text="📄 Results",
                bootstyle="success"
            )
        else:
            result_frame = ttkb.LabelFrame(parent, text="Results")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Text widget with scrollbar (with padding)
        text_container = ttkb.Frame(result_frame, padding=10)
        text_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttkb.Scrollbar(text_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.result_text = tk.Text(
            text_container,
            wrap=tk.WORD,
            font=('Consolas', 10),
            height=12,
            yscrollcommand=scrollbar.set,
            state='disabled',
            bg='#1e2a35' if HAS_BOOTSTRAP else 'white',
            fg='#ecf0f1' if HAS_BOOTSTRAP else 'black',
            insertbackground='white',
            padx=10,
            pady=10
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.result_text.yview)

    def create_action_buttons(self, parent):
        """Create action buttons"""
        btn_frame = ttkb.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=5)

        if HAS_BOOTSTRAP:
            self.copy_btn = ttkb.Button(
                btn_frame,
                text="📋 Copy to Clipboard",
                command=self.copy_results,
                bootstyle="primary-outline",
                width=18,
                state='disabled'
            )
            self.save_btn = ttkb.Button(
                btn_frame,
                text="💾 Save to File",
                command=self.save_results,
                bootstyle="secondary-outline",
                width=15,
                state='disabled'
            )
            self.clear_btn = ttkb.Button(
                btn_frame,
                text="🗑️ Clear",
                command=self.clear_results,
                bootstyle="danger-outline",
                width=10
            )
        else:
            self.copy_btn = ttkb.Button(
                btn_frame,
                text="Copy to Clipboard",
                command=self.copy_results,
                width=18,
                state='disabled'
            )
            self.save_btn = ttkb.Button(
                btn_frame,
                text="Save to File",
                command=self.save_results,
                width=15,
                state='disabled'
            )
            self.clear_btn = ttkb.Button(
                btn_frame,
                text="Clear",
                command=self.clear_results,
                width=10
            )

        self.copy_btn.pack(side=tk.LEFT, padx=5)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        self.clear_btn.pack(side=tk.RIGHT, padx=5)

    def create_status_bar(self, parent):
        """Create status bar"""
        self.status_var = tk.StringVar(value="Ready - Drop screenshot or click Browse")

        if HAS_BOOTSTRAP:
            status = ttkb.Label(
                parent,
                textvariable=self.status_var,
                font=("Segoe UI", 9),
                bootstyle="secondary"
            )
        else:
            status = ttkb.Label(
                parent,
                textvariable=self.status_var,
                font=("Segoe UI", 9)
            )
        status.pack(fill=tk.X, pady=(10, 0))

    def setup_dnd(self):
        """Setup drag and drop handlers"""
        self.drop_canvas.drop_target_register(DND_FILES)
        self.drop_canvas.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        """Handle dropped files"""
        # Parse file path (handle Windows paths with spaces)
        file_path = event.data.strip('{}')

        # Handle multiple files - take first one
        if '{' in file_path:
            files = [f.strip('{}') for f in file_path.split('} {')]
            file_path = files[0]

        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')):
            self.load_file(file_path)
        else:
            self.update_status("Invalid file type. Please drop an image file.", error=True)

    def browse_file(self):
        """Open file browser"""
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            title="Select Screenshot",
            initialdir=SCREENSHOTS_DIR if os.path.exists(SCREENSHOTS_DIR) else os.path.expanduser("~"),
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        """Load and preview file"""
        self.current_file = file_path
        filename = os.path.basename(file_path)

        # Update file label
        file_size = os.path.getsize(file_path) / 1024
        self.file_label.config(text=f"📄 {filename} ({file_size:.1f} KB)")

        # Auto-detect carrier from filename
        carrier = get_carrier_from_filename(filename)
        if carrier:
            self.carrier_var.set(carrier)
        else:
            self.carrier_var.set("Auto-detect")

        # Show image preview if PIL available
        if HAS_PIL:
            try:
                img = Image.open(file_path)
                # Create thumbnail
                img.thumbnail((780, 100), Image.Resampling.LANCZOS)
                self.image_reference = ImageTk.PhotoImage(img)

                # Update canvas
                self.drop_canvas.delete("all")
                self.drop_canvas.create_image(
                    390, 60,
                    anchor='center',
                    image=self.image_reference
                )
            except Exception:
                self.drop_canvas.delete("all")
                self.drop_canvas.create_text(
                    400, 60,
                    text=f"📄 {filename}\n(Preview not available)",
                    font=("Segoe UI", 11),
                    fill='#a0b0c0',
                    justify='center'
                )
        else:
            self.drop_canvas.delete("all")
            self.drop_canvas.create_text(
                400, 60,
                text=f"📄 {filename}",
                font=("Segoe UI", 12),
                fill='#a0b0c0',
                justify='center'
            )

        # Enable process button
        self.process_btn.config(state='normal')
        self.update_status(f"Loaded: {filename}")

        # Auto-process
        self.process_current_file()

    def process_current_file(self):
        """Process the current file"""
        if not self.current_file:
            return

        self.update_status("Processing...")
        self.process_btn.config(state='disabled')

        # Run in thread
        thread = threading.Thread(target=self._process_thread)
        thread.start()

    def _process_thread(self):
        """Background processing thread"""
        try:
            if not self.ocr.is_available():
                self.root.after(0, lambda: self._show_error("Tesseract OCR not installed"))
                return

            # Extract text
            text_lines = self.ocr.extract_text(self.current_file)
            if not text_lines:
                self.root.after(0, lambda: self._show_error("No text extracted from image"))
                return

            # Get carrier
            carrier = self.carrier_var.get()
            if carrier == "Auto-detect":
                carrier = detect_carrier('\n'.join(text_lines))

            self.current_carrier = carrier

            # Parse schedules
            schedules = parse_schedules(text_lines, carrier)

            if not schedules:
                self.root.after(0, lambda: self._show_error("No schedules found. Try different image or Edit mode."))
                return

            self.root.after(0, lambda: self._show_results(schedules, carrier))

        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

    def _show_results(self, schedules, carrier):
        """Display results"""
        self.current_schedules = schedules

        # Format output
        table = format_table(schedules)
        email = format_email(schedules)

        # Display
        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"Carrier: {carrier or 'Unknown'}\n")
        self.result_text.insert(tk.END, f"Found: {len(schedules)} schedule(s)\n")
        self.result_text.insert(tk.END, "=" * 50 + "\n\n")
        self.result_text.insert(tk.END, table + "\n\n")
        self.result_text.insert(tk.END, "EMAIL FORMAT:\n")
        self.result_text.insert(tk.END, "-" * 40 + "\n")
        self.result_text.insert(tk.END, email)
        self.result_text.config(state='disabled')

        # Enable buttons
        self.copy_btn.config(state='normal')
        self.save_btn.config(state='normal')
        self.process_btn.config(state='normal')

        self.update_status(f"Found {len(schedules)} schedule(s) - Ready to copy!")

    def _show_error(self, message):
        """Show error"""
        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"❌ Error: {message}\n\n")
        self.result_text.insert(tk.END, "Tips:\n")
        self.result_text.insert(tk.END, "- Make sure screenshot is clear and readable\n")
        self.result_text.insert(tk.END, "- Try a different carrier setting\n")
        self.result_text.insert(tk.END, "- Use CLI version with Edit mode for manual correction")
        self.result_text.config(state='disabled')

        self.process_btn.config(state='normal')
        self.update_status(f"Error: {message}", error=True)

    def copy_results(self):
        """Copy to clipboard"""
        if not self.current_schedules:
            return

        email_text = format_email(self.current_schedules)
        if copy_to_clipboard(email_text):
            self.update_status("✓ Copied to clipboard!")
            # Visual feedback
            orig_text = self.copy_btn.cget('text')
            self.copy_btn.config(text="✓ Copied!")
            self.root.after(2000, lambda: self.copy_btn.config(text=orig_text))
        else:
            # Fallback to tkinter clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(email_text)
            self.update_status("✓ Copied to clipboard!")

    def save_results(self):
        """Save to file"""
        if not self.current_schedules:
            return

        saved_path = save_output(self.current_schedules, OUTPUT_DIR, self.current_carrier)
        rel_path = os.path.relpath(saved_path, os.path.dirname(OUTPUT_DIR))
        self.update_status(f"✓ Saved: {rel_path}")

    def clear_results(self):
        """Clear everything"""
        self.current_file = None
        self.current_schedules = []
        self.current_carrier = None
        self.image_reference = None

        # Reset drop zone
        self.drop_canvas.delete("all")
        self.drop_text_id = self.drop_canvas.create_text(
            400, 60,
            text="🖼️  Drag & Drop Screenshot Here\nor click Browse button below",
            font=("Segoe UI", 12),
            fill='#a0b0c0',
            justify='center'
        )

        # Reset labels and text
        self.file_label.config(text="No file selected")
        self.carrier_var.set("Auto-detect")

        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state='disabled')

        # Disable buttons
        self.process_btn.config(state='disabled')
        self.copy_btn.config(state='disabled')
        self.save_btn.config(state='disabled')

        self.update_status("Ready - Drop screenshot or click Browse")

    def update_status(self, message, error=False):
        """Update status bar"""
        self.status_var.set(message)

    def run(self):
        """Start application"""
        self.root.mainloop()


def main():
    app = ScheduleParserGUI()
    app.run()


if __name__ == "__main__":
    main()
