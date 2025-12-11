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
from image_processor import ImageProcessor


class Clip2lGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Clip2l GUI — Batch Image Processor")
        self.root.geometry("750x700")
        self.processing = False
        self.selected_files = []

        # Configure style
        style = ttk.Style()
        style.theme_use('clam')

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
        
        self.files_listbox = tk.Listbox(main_frame, height=4, width=80)
        self.files_listbox.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        scrollbar.grid(row=2, column=3, sticky=(tk.N, tk.S))
        self.files_listbox.config(yscrollcommand=scrollbar.set)

        btn_add = ttk.Button(main_frame, text="Add Files", command=self.add_files)
        btn_add.grid(row=3, column=0, sticky=tk.W, padx=(0, 5))
        btn_clear = ttk.Button(main_frame, text="Clear List", command=self.clear_files)
        btn_clear.grid(row=3, column=1, sticky=tk.W)

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

        self.sequence_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Sequence Mode (concatenate & slice across images)", 
                        variable=self.sequence_var).grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 5))

        self.btn_generate = ttk.Button(btn_frame, text="Generate", command=self.generate)
        self.btn_generate.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_cancel = ttk.Button(btn_frame, text="Cancel", command=self.cancel, state=tk.DISABLED)
        self.btn_cancel.pack(side=tk.LEFT, padx=(0, 5))

        btn_exit = ttk.Button(btn_frame, text="Exit", command=root.quit)
        btn_exit.pack(side=tk.LEFT)

        # Output log
        ttk.Label(main_frame, text="Log Output:", font=("Arial", 10, "bold")).grid(row=11, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=12, width=80, state=tk.DISABLED)
        self.log_text.grid(row=12, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Configure grid weights for resizing
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(12, weight=1)

    def add_files(self):
        """Add files to the list."""
        files = filedialog.askopenfilenames(
            title="Select image files",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        for f in files:
            if f not in self.selected_files:
                self.selected_files.append(f)
        self.update_files_list()

    def clear_files(self):
        """Clear the file list."""
        self.selected_files = []
        self.update_files_list()

    def update_files_list(self):
        """Update the listbox display."""
        self.files_listbox.delete(0, tk.END)
        for f in self.selected_files:
            self.files_listbox.insert(tk.END, f)

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

    def generate(self):
        """Start image processing in a worker thread."""
        if self.processing:
            messagebox.showwarning("Already Processing", "Processing is already in progress.")
            return

        if not self.selected_files:
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
        self.log(f"Starting processing: {len(self.selected_files)} file(s)")
        self.log(f"Mode: {'Sequence' if self.sequence_var.get() else 'Individual'}")
        self.log(f"Output: {output_dir}")
        self.log(f"Width: {width}, Height: {height}")
        self.log("-" * 60)

        # Update UI
        self.processing = True
        self.btn_generate.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL)

        # Start worker thread
        thread = threading.Thread(
            target=self._process_images,
            args=(self.selected_files, output_dir, width, height, self.sequence_var.get()),
            daemon=True
        )
        thread.start()

    def _process_images(self, files, output_dir, width, height, sequence):
        """Worker function to process images."""
        try:
            processor = ImageProcessor(width, height)
            
            if sequence:
                generated = processor.process_sequence_list(files, output_dir)
            else:
                generated = processor.process_image_list(files, output_dir)

            self.log("")
            self.log(f"✓ Processing complete!")
            self.log(f"Generated {len(generated)} file(s) in:")
            self.log(output_dir)
            
            self.processing = False
            self.btn_generate.config(state=tk.NORMAL)
            self.btn_cancel.config(state=tk.DISABLED)
            
            messagebox.showinfo("Success", f"Processing complete!\nGenerated {len(generated)} file(s).")
        except Exception as e:
            self.log("")
            self.log(f"✗ Error: {str(e)}")
            self.processing = False
            self.btn_generate.config(state=tk.NORMAL)
            self.btn_cancel.config(state=tk.DISABLED)
            messagebox.showerror("Processing Error", str(e))

    def cancel(self):
        """Cancel processing (placeholder)."""
        messagebox.showinfo("Cancel", "Cancellation not yet fully implemented.\nPlease wait for processing to complete.")


if __name__ == "__main__":
    root = tk.Tk()
    app = Clip2lGUI(root)
    root.mainloop()
