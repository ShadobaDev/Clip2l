# Clip2l

A command-line tool for processing comic images for web publishing platforms (e.g., Webtoon).

## Features
- Batch resize and split images to fit publisher requirements
- Supports JPG and PNG input
- Output images with custom width and max height (default: 800x1280)
- Maintains reading order (by filename or list file)
- Output files named with 3-digit prefix and original filename
- Easy integration as a Python module

## Usage

### Command-line
```powershell
python Clip2l.py -i <input_dir> -o <output_dir> [-w <width>] [-H <height>] [-l <list_file>] [-s]
```
- `-i`, `--input`: Input directory with images or a text file with image paths
- `-o`, `--output`: Output directory for processed images
- `-w`, `--width`: Target width (default: 800)
- `-H`, `--height`: Max height per output image (default: 1280)
- `-l`, `--list-file`: Optional text file with image paths in order
- `-s`, `--sequence`: Sequence mode — concatenate images and slice across boundaries

### Command-line Examples
```powershell
# Process all images in a directory
python Clip2l.py -i input -o output -w 800 -H 1280

# Process images from a list file with custom dimensions
python Clip2l.py -l images.txt -o output -w 1024 -H 1536

# Process as sequence (images are concatenated vertically then sliced)
python Clip2l.py -i input -o output -w 800 -H 1280 -s
```

### Graphical Interface (Experimental)
```powershell
python gui_tkinter.py
```
- Tkinter-based GUI for interactive image processing
- Select files, configure output directory and dimensions
- Toggle sequence mode via checkbox
- View processing logs in real-time

## Project structure
- `Clip2l.py` — main CLI script
- `image_processor/` — core image processing module
- `gui_tkinter.py` — experimental Tkinter GUI interface (local development only)
- `test/` — test scripts and sample images

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

You are free to use, modify, and distribute this software for any purpose (personal, educational, or commercial) without restrictions.

## Dependencies

All dependencies use permissive open-source licenses (MIT, Apache-2.0, BSD). Run `python -m piplicenses` to view the full license list.

