# Clip2l: AI Agent Coding Instructions

## Project Overview

**Clip2l** is a Python CLI tool for batch processing comic images for web publishing platforms (e.g., Webtoon). It resizes images to a target width and splits them vertically if they exceed a max height. Output files preserve order with 3-digit zero-padded postfixes (`name_001.png`, `name_002.png`, etc.) across multiple input images.

### Key Architecture
- **`Clip2l.py`** — CLI entry point with argparse; delegates to `ImageProcessor`
- **`image_processor/image_processor.py`** — Core `ImageProcessor` class with three processing modes:
  - `process_image(path, output_dir, start_postfix)` → `(List[str], int)` — processes one image, returns generated files and next postfix
  - `process_image_list(image_list, output_dir)` → `List[str]` — batch processes a list of images with continuous postfix numbering
  - `process_directory(input_dir, output_dir)` → `List[str]` — batch processes all images in a directory (sorted by filename)

## Critical Workflows

### Running Tests
```powershell
# Test single image processing (uses test/007_1.png)
python test/test_image_processor.py

# Test directory processing with auto-generated images (output to test/generated_test/output)
python test/test_process_directory.py

# Test directory processing with user-supplied images (expects test/user_input; outputs to test/user_output)
python test/test_process_directory_userinput.py
```

### Running the CLI
```powershell
# Process all images in a directory
python Clip2l.py -i input_dir -o output_dir -w 800 -h 1280

# Process specific images in order (from list file)
python Clip2l.py -i list.txt -l list.txt -o output_dir
```

## Project-Specific Patterns & Conventions

### 1. Postfix Numbering (Recent API Change)
- **Pattern**: Use **postfix (suffix)** numbering, not prefix. Output format: `{basename}_{postfix:03d}.png` (e.g., `page_001.png`, `page_002.png`).
- **Why**: Preserves original filename semantics; improves readability across multiple input images.
- **API Change**: `process_image()` now returns a tuple `(generated_files, next_postfix)` to enable continuous numbering across batches.
  - Example: if `a.png` generates 2 files (postfixes 1–2), the next image starts at postfix 3.
  - `process_image_list()` consumes this returned postfix and passes it to the next image.

### 2. Image Mode Handling (Robust RGB Conversion)
- **Pattern**: Normalize all image inputs to RGB before resizing/slicing.
- **Implementation** (`image_processor.py`, lines 34–46):
  - RGBA/LA modes: convert to RGBA, composite alpha on white background, then to RGB.
  - Paletted images (mode 'P'): convert to RGBA with white background, then to RGB.
  - Other modes: direct `convert('RGB')`.
- **Why**: Prevents palette corruption or unexpected solid-color outputs; handles transparency predictably.

### 3. Directory Processing (Sorted Input)
- **Pattern**: `process_directory()` reads and sorts image filenames lexicographically before processing.
- **Example**: Given `b.png`, `a.png`, processes as `a.png` then `b.png`.
- **Implication**: Tests rely on sorted filenames for deterministic ordering; preserve this behavior.

### 4. Test Organization
- **Generated test** (`test/test_process_directory.py`):
  - Creates synthetic images in `test/generated_test/input/` (different colors for `a` and `b`).
  - Cleans input before test; leaves output for inspection.
  - Asserts expected filenames: `a_001.png`, `a_002.png`, `b_003.png`, etc.
- **User test** (`test/test_process_directory_userinput.py`):
  - Expects user-supplied images in `test/user_input/`.
  - Skips gracefully if no images present.
  - Outputs to `test/user_output/` for manual verification.

## Data Flow & Dependencies

1. **Input**: Directory of images or list file (paths with orderings).
2. **Core Processing**: Resize (maintain aspect ratio), then split vertically into slices.
3. **Output**: Sequential PNG files with 3-digit postfixes in output directory.
4. **Dependencies**: `PIL` (Pillow), `math`, `argparse`, `os`.

## Key Files & Their Purpose

| File | Purpose |
|------|---------|
| `Clip2l.py` | CLI interface; arg parsing and delegation |
| `image_processor/image_processor.py` | Core resize/slice logic; postfix numbering |
| `image_processor/__init__.py` | Module exports (`ImageProcessor` class) |
| `test/test_image_processor.py` | Single-image test |
| `test/test_process_directory.py` | Auto-generated directory test (sorted input) |
| `test/test_process_directory_userinput.py` | User-supplied image test (skip if empty) |

## When Modifying the Codebase

1. **Postfix logic**: Changes to numbering must preserve tuple return from `process_image()` and consume it in `process_image_list()`.
2. **Image processing**: Test with both transparent (RGBA) and paletted (GIF/PNG) inputs to ensure `ImageProcessor` handles all modes.
3. **Tests**: Update expected filenames if postfix format changes (currently `{name}_{num:03d}.png`).
4. **CLI**: Keep argparse interface stable; defaults are `width=800`, `height=1280`.

## Implementation Notes

- **Aspect ratio preservation**: Resize is width-first; height is computed from aspect ratio.
- **Slicing logic**: Uses `math.ceil(new_height / target_height)` to determine slice count; last slice may be shorter.
- **Output format**: Always PNG; hardcoded in `slice_img.save(output_path, "PNG")`.
- **Error handling**: Minimal; relies on exceptions from PIL and OS for file issues (consider adding validation if needed).

## Git Commit Message Format

Follow this convention for all commits:

```
type(module): brief description

detailed explanation
```

### Format Rules
- **type**: `fix`, `feat`, `doc`, `refactor`, `test`, `chore`
- **module**: File, function, or module name (e.g., `image_processor`, `CLI`, `test_process_directory`)
- **brief**: Single sentence, ideally under 50 characters
- **details**: Extended explanation (max 300 characters), optional but encouraged for non-trivial changes

### Examples
```
feat(image_processor): add postfix numbering for continuous output

Changed process_image() to return (files, next_postfix) tuple enabling
sequential numbering across multiple images without gaps or resets.

fix(test_process_directory): clean input before test

Prevents test failures from leftover input files; output preserved for inspection.

doc(copilot-instructions): document postfix API and test organization

Clarifies recent API changes and test structure for AI agents.
```
