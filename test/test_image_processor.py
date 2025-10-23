import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from image_processor import ImageProcessor

def test_process_image():
    # Ustawienia testowe
    input_image = os.path.join(os.path.dirname(__file__), '007_1.png')
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    width = 800
    height = 1280

    # Usuń katalog output jeśli istnieje
    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, f))
        os.rmdir(output_dir)

    processor = ImageProcessor(width, height)
    generated = processor.process_image(input_image, output_dir, 1)

    print('Wygenerowane pliki:')
    for f in generated:
        print(f)
    assert all(os.path.exists(f) for f in generated), 'Nie wszystkie pliki zostały wygenerowane.'
    print('Test zakończony sukcesem.')

if __name__ == '__main__':
    test_process_image()
