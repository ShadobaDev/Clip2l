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
    generated, next_postfix = processor.process_image(input_image, output_dir, 1)

    print('Wygenerowane pliki:')
    for f in generated:
        print(f)
    assert all(os.path.exists(f) for f in generated), 'Nie wszystkie pliki zostały wygenerowane.'
    assert isinstance(next_postfix, int) and next_postfix > 1, 'Nieprawidłowy next_postfix.'
    print('Test zakończony sukcesem.')


def test_process_image_jpg_format():
    input_image = os.path.join(os.path.dirname(__file__), '007_1.png')
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    width = 800
    height = 1280

    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, f))
        os.rmdir(output_dir)

    processor = ImageProcessor(width, height)
    generated, _ = processor.process_image(input_image, output_dir, 1, output_format='jpg')

    assert all(os.path.exists(f) for f in generated), 'Nie wszystkie pliki zostały wygenerowane.'
    assert all(f.lower().endswith('.jpg') for f in generated), 'Nie wszystkie pliki są w formacie JPG.'
    print('Test JPG format zakończony sukcesem.')


def test_process_image_jpg_compression():
    input_image = os.path.join(os.path.dirname(__file__), '007_1.png')
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    width = 800
    height = 1280

    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, f))
        os.rmdir(output_dir)

    processor = ImageProcessor(width, height, output_format='jpg', jpeg_quality=70, jpeg_subsampling=2, jpeg_optimize=True, jpeg_progressive=False)
    generated, _ = processor.process_image(input_image, output_dir, 1)

    assert all(os.path.exists(f) for f in generated), 'Nie wszystkie pliki zostały wygenerowane.'
    assert all(f.lower().endswith('.jpg') for f in generated), 'Nie wszystkie pliki są w formacie JPG.'
    print('Test JPG compression options zakończony sukcesem.')


if __name__ == '__main__':
    test_process_image()
    test_process_image_jpg_format()
    test_process_image_jpg_compression()
