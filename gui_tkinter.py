"""
Clip2l GUI — Tkinter-based graphical interface for image processing.

Tkinter is part of Python standard library (no additional dependencies).
Run with: python gui_tkinter.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from pathlib import Path
from PIL import Image, ImageTk
from image_processor import ImageProcessor

# Try to import sv_ttk theme; fall back gracefully if not available
try:
    import sv_ttk
    HAS_SV_TTK = True
except ImportError:
    HAS_SV_TTK = False


class ReorderableImageList(ttk.Frame):
    """Custom widget for displaying and reordering image files with thumbnails."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.images = []  # list of (filepath, PhotoImage) tuples
        self.photo_references = []  # keep references to PhotoImage objects
        
        # Create a canvas with scrollbar
        self.canvas = tk.Canvas(self, bg="gray20", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind canvas resize to update scrollable_frame width
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Bind mouse wheel to scroll (on entire widget)
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-4>", self._on_mousewheel)
        self.bind("<Button-5>", self._on_mousewheel)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<Button-4>", self._on_mousewheel)
        self.scrollable_frame.bind("<Button-5>", self._on_mousewheel)
    
    def _on_canvas_resize(self, event):
        """Update scrollable_frame width to match canvas width."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window_id, width=canvas_width)
        
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
    
    def _bind_scroll_recursive(self, widget):
        """Recursively bind mouse wheel events to widget and all its children."""
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)
        for child in widget.winfo_children():
            self._bind_scroll_recursive(child)
    
    def add_image(self, filepath):
        """Add an image file to the list."""
        if filepath not in [img[0] for img in self.images]:
            try:
                # Create thumbnail (60x60)
                img = Image.open(filepath)
                img.thumbnail((60, 60), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photo_references.append(photo)  # keep reference
                self.images.append((filepath, photo))
                self._redraw()
            except Exception as e:
                print(f"Error loading image {filepath}: {e}")

    def add_images(self, filepaths):
        """Add multiple image files to the list in one update."""
        existing_paths = {img[0] for img in self.images}
        new_items = []

        for filepath in filepaths:
            if filepath in existing_paths:
                continue
            try:
                img = Image.open(filepath)
                img.thumbnail((60, 60), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photo_references.append(photo)
                new_items.append((filepath, photo))
                existing_paths.add(filepath)
            except Exception as e:
                print(f"Error loading image {filepath}: {e}")

        if new_items:
            self.images.extend(new_items)
            self._redraw()
    
    def clear(self):
        """Clear all images."""
        self.images = []
        self.photo_references = []
        self._redraw()
    
    def get_image_list(self):
        """Return list of image filepaths in current order."""
        return [img[0] for img in self.images]
    
    def reverse(self):
        """Reverse the order of images."""
        self.images.reverse()
        self._redraw()
    
    def sort_by(self, sort_type: str):
        """
        Sort images by specified criteria.
        
        Args:
            sort_type (str): 'name', 'modified', or 'created'
        """
        import os
        from datetime import datetime
        
        if sort_type == "name":
            self.images.sort(key=lambda x: os.path.basename(x[0]))
        elif sort_type == "modified":
            self.images.sort(key=lambda x: os.path.getmtime(x[0]))
        elif sort_type == "created":
            # Windows: creation time; Unix: use birthtime if available, else modified
            self.images.sort(key=lambda x: os.path.getctime(x[0]))
        self._redraw()
    
    def _move_up(self, index):
        """Move image up in the list."""
        if index > 0:
            self.images[index], self.images[index - 1] = self.images[index - 1], self.images[index]
            self._redraw()
    
    def _move_down(self, index):
        """Move image down in the list."""
        if index < len(self.images) - 1:
            self.images[index], self.images[index + 1] = self.images[index + 1], self.images[index]
            self._redraw()
    
    def _remove_image(self, index):
        """Remove image from the list."""
        if 0 <= index < len(self.images):
            self.images.pop(index)
            self.photo_references.pop(index)
            self._redraw()
    
    def _redraw(self):
        """Redraw the list of images."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Update scrollable_frame width to match canvas width
        self.scrollable_frame.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        if canvas_width > 1:  # avoid initial small value
            self.canvas.itemconfig(self.canvas_window_id, width=canvas_width)
        
        for idx, (filepath, photo) in enumerate(self.images):
            # Create frame for each image item (full width)
            item_frame = ttk.Frame(self.scrollable_frame, relief=tk.SUNKEN, borderwidth=1)
            item_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
            
            # Thumbnail
            img_label = tk.Label(item_frame, image=photo, bg="gray20")
            img_label.pack(side=tk.LEFT, padx=5, pady=5)
            
            # Filename and path
            filename = Path(filepath).name
            info_frame = ttk.Frame(item_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            ttk.Label(info_frame, text=filename, font=("Arial", 10, "bold")).pack(anchor=tk.W)
            ttk.Label(info_frame, text=filepath, font=("Arial", 8), foreground="gray").pack(anchor=tk.W)
            
            # Buttons frame (up/down arrows) - fixed width, right-aligned
            btn_frame = ttk.Frame(item_frame, width=80)
            btn_frame.pack(side=tk.RIGHT, padx=5, pady=5)
            # btn_frame.pack_propagate(False)  # prevent frame from shrinking, commented beacuse of interference with button layout
            
            # Up button
            if idx > 0:
                btn_up = ttk.Button(btn_frame, text="ᐃ", width=3,
                                   command=lambda i=idx: self._move_up(i))
                btn_up.pack(side=tk.LEFT, padx=2)
            else:
                btn_up_placeholder = ttk.Button(btn_frame, text="ᐃ", width=3, state=tk.DISABLED)
                btn_up_placeholder.pack(side=tk.LEFT, padx=2)
            
            # Down button
            if idx < len(self.images) - 1:
                btn_down = ttk.Button(btn_frame, text="ᐁ", width=3,
                                     command=lambda i=idx: self._move_down(i))
                btn_down.pack(side=tk.LEFT, padx=2)
            else:
                btn_down_placeholder = ttk.Button(btn_frame, text="ᐁ", width=3, state=tk.DISABLED)
                btn_down_placeholder.pack(side=tk.LEFT, padx=2)
            
            # Delete button
            btn_delete = ttk.Button(btn_frame, text="⨉", width=3,
                                   command=lambda i=idx: self._remove_image(i))
            btn_delete.pack(side=tk.LEFT, padx=2)
        
        # Bind scroll events to all newly created widgets
        self._bind_scroll_recursive(self.scrollable_frame)


class Clip2lGUI:
    # Spinner frames for animation
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, root):
        self.root = root
        self.root.title("Clip2l GUI — Batch Image Processor")
        self.root.geometry("750x700")
        self.processing = False
        self.spinner_running = False
        self.spinner_thread = None
        self.spinner_index = 0

        # Configure style with Sun Valley theme (or fall back to 'clam')
        style = ttk.Style()
        if HAS_SV_TTK:
            sv_ttk.set_theme("dark")  # use "dark" or "light" theme variant
        else:
            style.theme_use("clam")  # fallback theme if sv_ttk not available
        
        # Main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Title
        title = ttk.Label(main_frame, text="Clip2l — Batch Image Processor", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # Input files section
        ttk.Label(main_frame, text="Input Images:", font=("Arial", 10, "bold")).grid(row=1, column=0, columnspan=3, sticky=tk.W)
        
        self.image_list = ReorderableImageList(main_frame, height=150)
        self.image_list.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))

        # Toolbar for image list
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        btn_add = ttk.Button(toolbar_frame, text="Add Files", command=self.add_files)
        btn_add.pack(side=tk.LEFT, padx=(0, 5))
        
        btn_clear = ttk.Button(toolbar_frame, text="Clear List", command=self.clear_files)
        btn_clear.pack(side=tk.LEFT, padx=(0, 5))
        
        btn_reverse = ttk.Button(toolbar_frame, text="Reverse Order", command=self.reverse_order)
        btn_reverse.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(toolbar_frame, text="Sort By:").pack(side=tk.LEFT, padx=(10, 5))
        
        self.sort_var = tk.StringVar(value="name")
        sort_combo = ttk.Combobox(toolbar_frame, textvariable=self.sort_var, 
                                  values=["name", "modified", "created"], 
                                  state="readonly", width=12)
        sort_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        btn_sort = ttk.Button(toolbar_frame, text="Sort", command=self.sort_images)
        btn_sort.pack(side=tk.LEFT)

        # Output directory section
        ttk.Label(main_frame, text="Output Directory:", font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        self.output_var = tk.StringVar(value=str(Path.home() / "Clip2l_output"))
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=60)
        output_entry.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
        btn_browse = ttk.Button(main_frame, text="Browse", command=self.browse_output)
        btn_browse.grid(row=5, column=2, sticky=tk.W, padx=(5, 0))

        # Processing options section
        ttk.Label(main_frame, text="Processing Options:", font=("Arial", 10, "bold")).grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        ttk.Label(main_frame, text="Target Width:").grid(row=7, column=0, sticky=tk.W)
        self.width_var = tk.StringVar(value="800")
        ttk.Entry(main_frame, textvariable=self.width_var, width=10).grid(row=7, column=1, sticky=tk.W)

        ttk.Label(main_frame, text="Target Height:").grid(row=8, column=0, sticky=tk.W)
        self.height_var = tk.StringVar(value="1280")
        ttk.Entry(main_frame, textvariable=self.height_var, width=10).grid(row=8, column=1, sticky=tk.W)

        ttk.Label(main_frame, text="Output Format:").grid(row=9, column=0, sticky=tk.W)
        self.format_var = tk.StringVar(value="png")
        format_combo = ttk.Combobox(main_frame, textvariable=self.format_var,
                                     values=["png", "jpg", "jpeg", "webp"],
                                     state="readonly", width=8)
        format_combo.grid(row=9, column=1, sticky=tk.W)

        # JPEG options: visible only when format is jpg/jpeg
        self.jpeg_options_frame = ttk.Frame(main_frame)
        self.jpeg_options_frame.grid(row=10, column=0, columnspan=2, sticky=tk.W, padx=(20,0), pady=(4,4))

        ttk.Label(self.jpeg_options_frame, text="JPEG Quality:").grid(row=0, column=0, sticky=tk.W)
        self.jpeg_quality_var = tk.IntVar(value=90)
        jpeg_quality_spin = ttk.Spinbox(self.jpeg_options_frame, from_=50, to=95, increment=1, textvariable=self.jpeg_quality_var, width=8)
        jpeg_quality_spin.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(self.jpeg_options_frame, text="JPEG Subsampling:").grid(row=1, column=0, sticky=tk.W)
        self.jpeg_subsampling_var = tk.StringVar(value="0")
        jpeg_subsampling_combo = ttk.Combobox(self.jpeg_options_frame, textvariable=self.jpeg_subsampling_var,
                                              values=["0", "1", "2"], state="readonly", width=8)
        jpeg_subsampling_combo.grid(row=1, column=1, sticky=tk.W)

        self.jpeg_optimize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.jpeg_options_frame, text="JPEG optimize", variable=self.jpeg_optimize_var).grid(row=2, column=0, columnspan=2, sticky=tk.W)

        self.jpeg_progressive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.jpeg_options_frame, text="JPEG progressive", variable=self.jpeg_progressive_var).grid(row=3, column=0, columnspan=2, sticky=tk.W)

        self.sequence_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Sequence Mode (concatenate & slice across images)", 
                        variable=self.sequence_var).grid(row=14, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

        # Visibility logic based on format selection
        def update_jpeg_options(*_):
            fmt = self.format_var.get().lower()
            if fmt in ("jpg", "jpeg"):
                self.jpeg_options_frame.grid()
            else:
                self.jpeg_options_frame.grid_remove()

        self.format_var.trace_add("write", update_jpeg_options)
        update_jpeg_options()

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=15, column=0, sticky=(tk.W), pady=(10, 3))

        self.btn_generate = ttk.Button(btn_frame, text="Generate", command=self.generate)
        self.btn_generate.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_cancel = ttk.Button(btn_frame, text="Cancel", command=self.cancel, state=tk.DISABLED)
        self.btn_cancel.pack(side=tk.LEFT, padx=(0, 5))

        btn_exit = ttk.Button(btn_frame, text="Exit", command=root.quit)
        btn_exit.pack(side=tk.LEFT)

        # Status frame with spinner (same row, stretches to the right)
        self.status_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=1)
        self.status_frame.grid(row=15, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 3), padx=(5, 0))
        
        self.spinner_label = tk.Label(self.status_frame, text="⠿", font=("Arial", 12, "bold"), fg="cyan")
        self.spinner_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.status_label = tk.Label(self.status_frame, text="Ready", font=("Arial", 10))
        self.status_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Output log
        ttk.Label(main_frame, text="Log Output:", font=("Arial", 10, "bold")).grid(row=16, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=12, width=80, state=tk.DISABLED)
        self.log_text.grid(row=17, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Configure grid weights for resizing
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(17, weight=1)

    def add_files(self):
        """Add files to the list."""
        files = filedialog.askopenfilenames(
            title="Select image files",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if files:
            # Start spinner
            self._start_spinner(f"Loading {len(files)} file(s)...")
            
            # Load files in a separate thread
            thread = threading.Thread(target=self._load_files_worker, args=(files,), daemon=True)
            thread.start()
    
    def _load_files_worker(self, files):
        """Worker thread to load files."""
        try:
            # Preserve the file order from user selection / sort, top-to-bottom.
            for f in files:
                self.image_list.add_image(f)
        finally:
            self._stop_spinner("Ready")

    def clear_files(self):
        """Clear the file list."""
        self.image_list.clear()

    def reverse_order(self):
        """Reverse the order of images in the list."""
        self.image_list.reverse()

    def sort_images(self):
        """Sort images by selected criteria."""
        sort_by = self.sort_var.get()
        self.image_list.sort_by(sort_by)

    def update_files_list(self):
        """Update the listbox display."""
        pass  # No longer needed; handled by ReorderableImageList

    def browse_output(self):
        """Browse for output directory."""
        folder = filedialog.askdirectory(title="Select output directory")
        if folder:
            self.output_var.set(folder)

    def log(self, message):
        """Append message to log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def _start_spinner(self, status_message):
        """Start spinner animation with status message."""
        self.spinner_running = True
        self.status_label.config(text=status_message)
        self.spinner_index = 0
        
        # Start spinner in a separate thread
        self.spinner_thread = threading.Thread(target=self._animate_spinner, daemon=True)
        self.spinner_thread.start()
    
    def _animate_spinner(self):
        """Animate the spinner."""
        while self.spinner_running:
            frame = self.SPINNER_FRAMES[self.spinner_index % len(self.SPINNER_FRAMES)]
            try:
                self.spinner_label.config(text=frame)
            except:
                pass  # window might be closed
            self.spinner_index += 1
            threading.Event().wait(0.1)  # 100ms between frames
    
    def _stop_spinner(self, final_message="Ready"):
        """Stop spinner animation."""
        self.spinner_running = False
        try:
            self.spinner_label.config(text="⠿")
            self.status_label.config(text=final_message)
        except:
            pass  # window might be closed
        if self.spinner_thread:
            self.spinner_thread.join(timeout=1)

    def generate(self):
        """Start image processing in a worker thread."""
        if self.processing:
            messagebox.showwarning("Already Processing", "Processing is already in progress.")
            return

        selected_files = self.image_list.get_image_list()
        if not selected_files:
            messagebox.showerror("No Files", "Please select at least one image file.")
            return

        output_dir = self.output_var.get().strip()
        if not output_dir:
            messagebox.showerror("No Output Dir", "Please specify an output directory.")
            return

        try:
            width = int(self.width_var.get().strip())
            height = int(self.height_var.get().strip())
            if width <= 0 or height <= 0:
                raise ValueError("Width and height must be positive integers.")
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Log start
        self.log(f"+" + "-" * 60 + "+")
        self.log(f"Starting processing: {len(selected_files)} file(s)")
        self.log(f"Mode: {'Sequence' if self.sequence_var.get() else 'Individual'}")
        self.log(f"Output: {output_dir}")
        self.log(f"Width: {width}, Height: {height}, Format: {self.format_var.get()}")
        self.log("-" * 60)

        # Update UI
        self.processing = True
        self.btn_generate.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL)
        
        # Start spinner
        self._start_spinner("Generating...")

        # Start worker thread
        thread = threading.Thread(
            target=self._process_images,
            args=(selected_files, output_dir, width, height, self.sequence_var.get()),
            daemon=True
        )
        thread.start()

    def _process_images(self, files, output_dir, width, height, sequence):
        """Worker function to process images."""
        try:
            processor = ImageProcessor(
                width,
                height,
                output_format=self.format_var.get(),
                jpeg_quality=self.jpeg_quality_var.get(),
                jpeg_subsampling=int(self.jpeg_subsampling_var.get()),
                jpeg_optimize=self.jpeg_optimize_var.get(),
                jpeg_progressive=self.jpeg_progressive_var.get(),
            )
            
            if sequence:
                generated = processor.process_sequence_list(files, output_dir, output_format=self.format_var.get())
            else:
                generated = processor.process_image_list(files, output_dir, output_format=self.format_var.get())

            self.log("")
            self.log(f"✓ Processing complete!")
            self.log(f"Generated {len(generated)} file(s) in:")
            self.log(output_dir)
            
            self.processing = False
            self.btn_generate.config(state=tk.NORMAL)
            self.btn_cancel.config(state=tk.DISABLED)
            
            self._stop_spinner("Done!")
            
            messagebox.showinfo("Success", f"Processing complete!\nGenerated {len(generated)} file(s).")
        except Exception as e:
            self.log("")
            self.log(f"✗ Error: {str(e)}")
            self.processing = False
            self.btn_generate.config(state=tk.NORMAL)
            self.btn_cancel.config(state=tk.DISABLED)
            
            self._stop_spinner("Error!")
            
            messagebox.showerror("Processing Error", str(e))

    def cancel(self):
        """Cancel processing (placeholder)."""
        messagebox.showinfo("Cancel", "Cancellation not yet fully implemented.\nPlease wait for processing to complete.")


if __name__ == "__main__":
    root = tk.Tk()
    app = Clip2lGUI(root)
    root.mainloop()
