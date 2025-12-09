import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from image_processor import ImageProcessor


def make_image(path: str, width: int, height: int, color=(255, 0, 0)):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new('RGB', (width, height), color)
    img.save(path, 'PNG')


def test_process_directory():
    base_dir = os.path.dirname(__file__)
    # Use a separate test directory so we don't touch the project's `test/input`.
    test_dir = os.path.join(base_dir, 'generated_test')
    input_dir = os.path.join(test_dir, 'input')
    output_dir = os.path.join(test_dir, 'output')

    # Clean input directory before test
    if os.path.exists(input_dir):
        for f in os.listdir(input_dir):
            os.remove(os.path.join(input_dir, f))
    else:
        os.makedirs(input_dir)

    # Create two test images sized so slices will be: a -> 2, b -> 3
    # Make them different colors to ensure output isn't a uniform red square.
    a_path = os.path.join(input_dir, 'a.png')
    b_path = os.path.join(input_dir, 'b.png')
    make_image(a_path, 100, 80, color=(0, 128, 255))   # blue-ish
    make_image(b_path, 100, 130, color=(0, 200, 0))    # green

    processor = ImageProcessor(target_width=100, target_height=50)
    generated = processor.process_directory(input_dir, output_dir)

    # Expected files in order (process_directory sorts input filenames):
    expected = [
        'a_001.png',
        'a_002.png',
        'b_003.png',
        'b_004.png',
        'b_005.png',
    ]

    # Collect basenames of generated files and sort by filename to compare order
    basenames = [os.path.basename(p) for p in generated]

    assert basenames == expected, f"Generated filenames mismatch: {basenames} != {expected}"
    assert all(os.path.exists(os.path.join(output_dir, f)) for f in expected), 'Some output files are missing.'


if __name__ == '__main__':
    test_process_directory()
    print('Directory processing test passed.')
