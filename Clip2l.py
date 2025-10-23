import sys
import argparse
import os
from image_processor import ImageProcessor

def parse_args():
    parser = argparse.ArgumentParser(description='Process comic pages for web publishing platforms')
    
    parser.add_argument('--input', '-i', required=True,
                       help='Input directory containing images or a text file with image paths')
    parser.add_argument('--output', '-o', required=True,
                       help='Output directory for processed images')
    parser.add_argument('--width', '-w', type=int, default=800,
                       help='Target width for output images (default: 800)')
    parser.add_argument('--height', '-h', type=int, default=1280,
                       help='Maximum height for output images (default: 1280)')
    parser.add_argument('--list-file', '-l', 
                       help='Optional text file containing image paths in order')
    
    return parser.parse_args()

def read_image_list(list_file):
    with open(list_file, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def main():
    args = parse_args()
    
    # Create image processor with target dimensions
    processor = ImageProcessor(args.width, args.height)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Process images based on input type
    if args.list_file:
        # Process images from list file
        image_list = read_image_list(args.list_file)
        generated_files = processor.process_image_list(image_list, args.output)
    else:
        # Process all images in directory
        generated_files = processor.process_directory(args.input, args.output)
    
    print(f"Processing complete. Generated {len(generated_files)} files:")
    for file in generated_files:
        print(f"  - {file}")

if __name__ == '__main__':
    main()