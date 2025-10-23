# image_processor module

This module provides the core image processing logic for the Clip2l project.

## Features
- Resize images to a target width while maintaining aspect ratio
- Split images vertically if they exceed a maximum height
- Output files are named with a 3-digit prefix and the original filename
- Supports batch processing from a directory or a list of files

## Usage

Import the `ImageProcessor` class:
```python
from image_processor import ImageProcessor
```

### Example
```python
processor = ImageProcessor(target_width=800, target_height=1280)
output_files = processor.process_image_list(["page1.png", "page2.jpg"], "output_dir")
```

## API
- `ImageProcessor(target_width, target_height)` — create processor
- `process_image(image_path, output_dir, prefix_num)` — process a single image
- `process_image_list(image_list, output_dir)` — process a list of images
- `process_directory(input_dir, output_dir)` — process all images in a directory
