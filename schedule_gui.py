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

from tkinter import messagebox

from core.config import SCREENSHOTS_DIR, OUTPUT_DIR, CARRIER_MAP, DEFAULT_BROWSE_DIR
from core.parsers import parse_schedules, get_carrier_from_filename, detect_carrier
from core.models import Schedule
from core.vessel_db import get_vessel_db, VesselDatabase
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
        self._cached_text_lines = None  # Cache OCR results for manual carrier selection

        # Initialize vessel database
        self.vessel_db = get_vessel_db()

        # Build UI
        self.create_widgets()

        # Update data source indicator after UI is built
        self._update_source_indicator()

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

        # Data source selector
        self.create_data_source_bar(main)

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

        # Left side - title and subtitle
        left_frame = ttkb.Frame(header_frame)
        left_frame.pack(side=tk.LEFT)

        if HAS_BOOTSTRAP:
            title = ttkb.Label(
                left_frame,
                text="📦 Schedule Parser by Geralcus",
                font=("Segoe UI", 18, "bold"),
                bootstyle="inverse-primary"
            )
        else:
            title = ttkb.Label(
                left_frame,
                text="Schedule Parser by Geralcus",
                font=("Segoe UI", 18, "bold")
            )
        title.pack(anchor='w')

        subtitle = ttkb.Label(
            left_frame,
            text="Convert schedule screenshots to text for email",
            font=("Segoe UI", 9)
        )
        subtitle.pack(anchor='w')

        # Right side info
        right_frame = ttkb.Frame(header_frame)
        right_frame.pack(side=tk.RIGHT)

        version = ttkb.Label(
            right_frame,
            text="v3.2.7",
            font=("Segoe UI", 10)
        )
        version.pack(anchor='e')

        # Changelog button
        if HAS_BOOTSTRAP:
            changelog_btn = ttkb.Button(
                right_frame,
                text="Changelog",
                command=self.show_changelog,
                bootstyle="link",
                width=10
            )
        else:
            changelog_btn = ttkb.Button(
                right_frame,
                text="Changelog",
                command=self.show_changelog,
                width=10
            )
        changelog_btn.pack(anchor='e')

        author = ttkb.Label(
            right_frame,
            text="GitHub: giangeralcus",
            font=("Segoe UI", 8)
        )
        author.pack(anchor='e')

    def create_data_source_bar(self, parent):
        """Create data source selector with status indicator"""
        source_frame = ttkb.Frame(parent)
        source_frame.pack(fill=tk.X, pady=(0, 10))

        # Left side - Data source label and selector
        left_frame = ttkb.Frame(source_frame)
        left_frame.pack(side=tk.LEFT)

        ttkb.Label(
            left_frame,
            text="Data Source:",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)

        self.source_var = tk.StringVar(value="cloud")
        sources = [("Cloud (Supabase)", "cloud"), ("Local (Offline)", "offline")]

        for text, value in sources:
            if HAS_BOOTSTRAP:
                rb = ttkb.Radiobutton(
                    left_frame,
                    text=text,
                    variable=self.source_var,
                    value=value,
                    command=self._on_source_change,
                    bootstyle="info-toolbutton"
                )
            else:
                rb = ttkb.Radiobutton(
                    left_frame,
                    text=text,
                    variable=self.source_var,
                    value=value,
                    command=self._on_source_change
                )
            rb.pack(side=tk.LEFT, padx=5)

        # Right side - Status indicator
        right_frame = ttkb.Frame(source_frame)
        right_frame.pack(side=tk.RIGHT)

        # Status indicator frame (colored box + text)
        self.indicator_frame = ttkb.Frame(right_frame)
        self.indicator_frame.pack(side=tk.RIGHT)

        # Status dot (canvas for colored circle)
        self.status_dot = tk.Canvas(
            self.indicator_frame,
            width=12,
            height=12,
            highlightthickness=0,
            bg=self.root.cget('bg') if not HAS_BOOTSTRAP else '#2b3e50'
        )
        self.status_dot.pack(side=tk.LEFT, padx=(0, 5))
        self.dot_id = self.status_dot.create_oval(2, 2, 10, 10, fill='gray', outline='')

        # Status text
        self.source_status_var = tk.StringVar(value="Connecting...")
        self.source_status_label = ttkb.Label(
            self.indicator_frame,
            textvariable=self.source_status_var,
            font=("Segoe UI", 9)
        )
        self.source_status_label.pack(side=tk.LEFT)

        # Vessel count label
        self.vessel_count_var = tk.StringVar(value="")
        self.vessel_count_label = ttkb.Label(
            self.indicator_frame,
            textvariable=self.vessel_count_var,
            font=("Segoe UI", 8)
        )
        self.vessel_count_label.pack(side=tk.LEFT, padx=(10, 0))

    def _on_source_change(self):
        """Handle data source change"""
        new_source = self.source_var.get()
        self.source_status_var.set("Switching...")
        self.status_dot.itemconfig(self.dot_id, fill='orange')
        self.root.update()

        # Switch mode in background
        def switch_thread():
            success = self.vessel_db.switch_mode(new_source)
            self.root.after(0, lambda: self._update_source_indicator())

        thread = threading.Thread(target=switch_thread)
        thread.start()

    def _update_source_indicator(self):
        """Update the source status indicator based on current connection"""
        stats = self.vessel_db.get_stats()
        mode = stats.get('mode', 'offline')
        vessels = stats.get('total_vessels', 0)
        aliases = stats.get('total_aliases', 0)

        # Update radio button to match actual mode
        if mode == 'cloud':
            self.source_var.set('cloud')
            self.source_status_var.set("Connected to Cloud")
            self.status_dot.itemconfig(self.dot_id, fill='#28a745')  # Green
        elif mode == 'docker':
            self.source_var.set('cloud')  # Docker is also "cloud" type
            self.source_status_var.set("Connected to Docker")
            self.status_dot.itemconfig(self.dot_id, fill='#17a2b8')  # Cyan
        elif mode == 'cache':
            self.source_var.set('offline')
            self.source_status_var.set("Using Local Cache")
            self.status_dot.itemconfig(self.dot_id, fill='#ffc107')  # Yellow
        else:
            self.source_var.set('offline')
            self.source_status_var.set("Offline Mode")
            self.status_dot.itemconfig(self.dot_id, fill='#6c757d')  # Gray

        # Update vessel count
        self.vessel_count_var.set(f"({vessels} vessels, {aliases} aliases)")

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

        # Priority: DEFAULT_BROWSE_DIR (Screenshots) > SCREENSHOTS_DIR > Home
        if os.path.exists(DEFAULT_BROWSE_DIR):
            initial_dir = DEFAULT_BROWSE_DIR
        elif os.path.exists(SCREENSHOTS_DIR):
            initial_dir = SCREENSHOTS_DIR
        else:
            initial_dir = os.path.expanduser("~")

        file_path = filedialog.askopenfilename(
            title="Select Screenshot",
            initialdir=initial_dir,
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        """Load and preview file with security validation"""
        filename = os.path.basename(file_path)

        # Security: Check file exists
        if not os.path.isfile(file_path):
            self.update_status("File not found or invalid", error=True)
            return

        # Security: File size limit (max 50MB to prevent DoS)
        MAX_FILE_SIZE_MB = 50
        file_size_bytes = os.path.getsize(file_path)
        file_size_kb = file_size_bytes / 1024
        file_size_mb = file_size_kb / 1024

        if file_size_mb > MAX_FILE_SIZE_MB:
            self.update_status(f"File too large ({file_size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB limit)", error=True)
            return

        # Security: Validate image magic bytes (not just extension)
        if not self._validate_image_magic(file_path):
            self.update_status("Invalid image file (corrupted or wrong format)", error=True)
            return

        self.current_file = file_path

        # Update file label
        self.file_label.config(text=f"📄 {filename} ({file_size_kb:.1f} KB)")

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

        # Check if we have cached text lines (user rejected auto-detect and chose manually)
        carrier = self.carrier_var.get()
        if hasattr(self, '_cached_text_lines') and self._cached_text_lines and carrier != "Auto-detect":
            # Use cached text lines instead of re-running OCR
            self._process_with_text(self._cached_text_lines, carrier)
            return

        # Run in thread
        thread = threading.Thread(target=self._process_thread)
        thread.start()

    def _process_thread(self):
        """Background processing thread with detailed error reporting"""
        try:
            # Step 1: Check OCR availability
            if not self.ocr.is_available():
                self.root.after(0, lambda: self._show_error(
                    "Tesseract OCR not installed",
                    "Install Tesseract: https://github.com/tesseract-ocr/tesseract"
                ))
                return

            # Step 2: Check file exists
            if not os.path.exists(self.current_file):
                filename = os.path.basename(self.current_file)
                self.root.after(0, lambda f=filename: self._show_error(
                    "File not found",
                    f"File: {f}"
                ))
                return

            # Step 3: Extract text with timeout
            text_lines = self.ocr.extract_text(self.current_file)

            if not text_lines:
                # Check why OCR failed
                from processors.image import ImageProcessor
                img_proc = ImageProcessor()
                img_info = img_proc.get_image_info(self.current_file)

                if not img_info:
                    reason = "Image file corrupt or unreadable"
                elif img_info.get('width', 0) < 100:
                    reason = f"Image too small ({img_info.get('width')}x{img_info.get('height')}px)"
                else:
                    reason = f"OCR could not extract text (image: {img_info.get('width')}x{img_info.get('height')}px)"

                self.root.after(0, lambda r=reason: self._show_error("No text extracted", r))
                return

            # Step 4: Check if carrier already selected manually
            carrier = self.carrier_var.get()

            if carrier != "Auto-detect":
                # User already selected carrier manually - skip confirmation
                self.current_carrier = carrier
                schedules = parse_schedules(text_lines, carrier)

                if not schedules:
                    sample_text = text_lines[:3] if len(text_lines) > 3 else text_lines
                    sample = '\n'.join(sample_text)[:150]
                    self.root.after(0, lambda s=sample: self._show_error(
                        "No schedules found",
                        f"Carrier: {carrier or 'Unknown'}\nOCR extracted {len(text_lines)} lines.\nSample:\n{s}..."
                    ))
                    return

                self.root.after(0, lambda: self._show_results(schedules, carrier))
            else:
                # Auto-detect carrier and show confirmation dialog
                detected_carrier = detect_carrier('\n'.join(text_lines))
                self.root.after(0, lambda: self._show_carrier_confirmation(detected_carrier, text_lines))

        except Exception as e:
            import traceback
            err_detail = traceback.format_exc().split('\n')[-2]
            self.root.after(0, lambda: self._show_error(f"Error: {str(e)}", err_detail))

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

    def _show_error(self, message, detail=None):
        """Show error with optional detail"""
        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"❌ {message}\n\n")

        if detail:
            self.result_text.insert(tk.END, f"Detail:\n{detail}\n\n")

        self.result_text.insert(tk.END, "-" * 40 + "\n")
        self.result_text.insert(tk.END, "Tips:\n")
        self.result_text.insert(tk.END, "- Screenshot harus jelas dan terbaca\n")
        self.result_text.insert(tk.END, "- Coba pilih carrier manual (bukan Auto-detect)\n")
        self.result_text.insert(tk.END, "- Pastikan format schedule sesuai (Maersk/OOCL/CMA)\n")
        self.result_text.insert(tk.END, "- Crop screenshot agar fokus ke tabel schedule")
        self.result_text.config(state='disabled')

        self.process_btn.config(state='normal')
        self.update_status(f"Error: {message}", error=True)

    def _show_carrier_confirmation(self, detected_carrier: str, text_lines: list):
        """Show carrier confirmation dialog before processing"""
        # Build dialog message
        if detected_carrier:
            msg = f"Carrier terdeteksi: {detected_carrier}\n\nLanjutkan dengan carrier ini?"
            title = "Konfirmasi Carrier"
        else:
            msg = "Carrier tidak terdeteksi.\n\nPilih carrier secara manual dari dropdown, lalu klik Process."
            title = "Carrier Tidak Dikenali"
            messagebox.showwarning(title, msg)
            self.process_btn.config(state='normal')
            return

        # Show Yes/No dialog
        result = messagebox.askyesno(title, msg)

        if result:
            # User confirmed - proceed with detected carrier
            self.carrier_var.set(detected_carrier)
            self._cached_text_lines = text_lines
            self._process_with_text(text_lines, detected_carrier)
        else:
            # User said No - let them choose manually
            self.update_status("Pilih carrier manual dari dropdown, lalu klik Process")
            self.process_btn.config(state='normal')
            # Store text lines for later use
            self._cached_text_lines = text_lines

    def _process_with_text(self, text_lines: list, carrier: str):
        """Process with already-extracted text lines"""
        try:
            schedules = []

            # ULTRATHINK: Try TSV + Bounding Box method first for Maersk
            # This provides better spatial analysis for multi-column tables
            if carrier == 'MAERSK' and self.current_file:
                tsv_schedules = self._try_tsv_maersk()
                if tsv_schedules:
                    schedules = tsv_schedules
                    logger.info(f"TSV method succeeded: {len(schedules)} schedules")

            # Fallback to text-based parsing
            if not schedules:
                schedules = parse_schedules(text_lines, carrier)

            if not schedules:
                # Show what was detected for debugging
                sample_text = text_lines[:3] if len(text_lines) > 3 else text_lines
                sample = '\n'.join(sample_text)[:150]
                self._show_error(
                    "No schedules found",
                    f"Carrier: {carrier or 'Unknown'}\nOCR extracted {len(text_lines)} lines.\nSample:\n{sample}..."
                )
                return

            self._show_results(schedules, carrier)

        except Exception as e:
            import traceback
            err_detail = traceback.format_exc().split('\n')[-2]
            self._show_error(f"Error: {str(e)}", err_detail)

    def _try_tsv_maersk(self) -> list:
        """
        Try TSV + Bounding Box method for Maersk schedules

        Uses spatial analysis to properly parse multi-column tables,
        filtering out Deadlines section.

        Returns:
            List of Schedule objects or empty list if failed
        """
        if not self.current_file:
            return []

        try:
            from core.vessel_db import match_vessel

            # Use OCR's TSV extraction method
            tsv_results = self.ocr.extract_maersk_schedules(self.current_file)

            if not tsv_results:
                return []

            # Convert to Schedule objects
            schedules = []
            for item in tsv_results:
                vessel_name = match_vessel(item['vessel'])
                schedules.append(Schedule(
                    vessel=vessel_name,
                    voyage=item['voyage'],
                    etd=item['departure'],
                    eta=item['arrival'],
                    carrier='MAERSK'
                ))

            return schedules

        except Exception as e:
            logger.warning(f"TSV method failed: {e}")
            return []

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
        self._cached_text_lines = None

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

    def _validate_image_magic(self, file_path):
        """Validate image file using magic bytes (not just extension)"""
        # Magic bytes for common image formats
        MAGIC_BYTES = {
            b'\x89PNG\r\n\x1a\n': 'PNG',
            b'\xff\xd8\xff': 'JPEG',
            b'GIF87a': 'GIF',
            b'GIF89a': 'GIF',
            b'BM': 'BMP',
            b'II*\x00': 'TIFF',
            b'MM\x00*': 'TIFF',
        }

        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)

            for magic, fmt in MAGIC_BYTES.items():
                if header.startswith(magic):
                    return True

            return False
        except Exception:
            return False

    def update_status(self, message, error=False):
        """Update status bar"""
        self.status_var.set(message)

    def show_changelog(self):
        """Show changelog in a popup window"""
        changelog_path = os.path.join(os.path.dirname(__file__), "CHANGELOG.md")

        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Changelog - Schedule Parser")
        popup.geometry("600x500")
        popup.transient(self.root)

        # Text widget with scrollbar
        frame = ttkb.Frame(popup, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttkb.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text = tk.Text(
            frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            yscrollcommand=scrollbar.set,
            bg='#1e2a35' if HAS_BOOTSTRAP else 'white',
            fg='#ecf0f1' if HAS_BOOTSTRAP else 'black',
            padx=10,
            pady=10
        )
        text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)

        # Load changelog content
        try:
            with open(changelog_path, 'r', encoding='utf-8') as f:
                content = f.read()
            text.insert(tk.END, content)
        except Exception as e:
            text.insert(tk.END, f"Error loading changelog: {e}")

        text.config(state='disabled')

        # Close button
        if HAS_BOOTSTRAP:
            close_btn = ttkb.Button(popup, text="Close", command=popup.destroy, bootstyle="secondary")
        else:
            close_btn = ttkb.Button(popup, text="Close", command=popup.destroy)
        close_btn.pack(pady=10)

    def run(self):
        """Start application"""
        self.root.mainloop()


def main():
    app = ScheduleParserGUI()
    app.run()


if __name__ == "__main__":
    main()
