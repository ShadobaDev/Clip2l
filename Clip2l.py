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
    parser.add_argument('--height', '-H', type=int, default=1280,
                       help='Maximum height for output images (default: 1280)')
    parser.add_argument('--list-file', '-l', 
                       help='Optional text file containing image paths in order')
    parser.add_argument('--sequence', '-s', action='store_true',
                       help='Treat inputs as a sequence: concatenate then slice across image boundaries')
    parser.add_argument('--format', '-f', default='png', choices=['png', 'jpg', 'jpeg', 'webp'],
                       help='Output image format (default: png)')
    parser.add_argument('--jpeg-quality', type=int, default=90,
                       help='JPEG quality (1-95, default 90)')
    parser.add_argument('--jpeg-subsampling', type=int, choices=[0, 1, 2], default=0,
                       help='JPEG subsampling (0=4:4:4,1=4:2:2,2=4:2:0, default 0)')
    parser.add_argument('--jpeg-optimize', dest='jpeg_optimize', action='store_true', default=True,
                       help='Enable JPEG optimization (default true)')
    parser.add_argument('--no-jpeg-optimize', dest='jpeg_optimize', action='store_false',
                       help='Disable JPEG optimization')
    parser.add_argument('--jpeg-progressive', dest='jpeg_progressive', action='store_true', default=False,
                       help='Use progressive JPEG output')
    parser.add_argument('--no-jpeg-progressive', dest='jpeg_progressive', action='store_false',
                       help='Do not use progressive JPEG output')
    
    return parser.parse_args()

def read_image_list(list_file):
    with open(list_file, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def main():
    args = parse_args()
    
    # Create image processor with target dimensions and output format
    processor = ImageProcessor(
        args.width,
        args.height,
        output_format=args.format,
        jpeg_quality=args.jpeg_quality,
        jpeg_subsampling=args.jpeg_subsampling,
        jpeg_optimize=args.jpeg_optimize,
        jpeg_progressive=args.jpeg_progressive,
    )
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Process images based on input type and mode
    if args.sequence:
        # Sequence mode: concatenate images then slice across seams
        if args.list_file:
            image_list = read_image_list(args.list_file)
        else:
            # read all files from directory (sorted)
            image_list = []
            for filename in sorted(os.listdir(args.input)):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_list.append(os.path.join(args.input, filename))
        generated_files = processor.process_sequence_list(image_list, args.output, start_postfix=1, output_format=args.format)
    else:
        if args.list_file:
            # Process images from list file
            image_list = read_image_list(args.list_file)
            generated_files = processor.process_image_list(image_list, args.output, output_format=args.format)
        else:
            # Process all images in directory
            generated_files = processor.process_directory(args.input, args.output, output_format=args.format)
    
    print(f"Processing complete. Generated {len(generated_files)} files:")
    for file in generated_files:
        print(f"  - {file}")

if __name__ == '__main__':
    main()