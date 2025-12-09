import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from image_processor import ImageProcessor


def test_process_directory_user_input():
    base_dir = os.path.dirname(__file__)
    # This directory is intended for user-supplied images. Do NOT generate images here.
    input_dir = os.path.join(base_dir, 'user_test/input')
    output_dir = os.path.join(base_dir, 'user_test/output')

    # Clean output directory before test
    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, f))
    else:
        os.makedirs(output_dir)

    # If the user hasn't provided images, skip the test (print informative message).
    if not os.path.exists(input_dir) or not any(os.path.isfile(os.path.join(input_dir, f)) for f in os.listdir(input_dir)):
        print(f"No user-supplied images found in '{input_dir}'. Skipping user-input directory test.")
        return

    processor = ImageProcessor(target_width=800, target_height=1280)
    generated = processor.process_directory(input_dir, output_dir)

    # Basic sanity checks: generated list is non-empty and output files exist
    assert isinstance(generated, list) and len(generated) > 0, 'No files were generated from user input.'
    assert all(os.path.exists(p) for p in generated), 'Some generated files are missing.'


if __name__ == '__main__':
    test_process_directory_user_input()
    print('User-input directory test completed (or skipped).')
