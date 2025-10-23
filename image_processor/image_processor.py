from PIL import Image
import os
from typing import List, Tuple, Optional
import math

class ImageProcessor:
    def __init__(self, target_width: int, target_height: int):
        """
        Initialize the image processor with target dimensions.
        
        Args:
            target_width (int): The target width for the output images
            target_height (int): The maximum height for each output image slice
        """
        self.target_width = target_width
        self.target_height = target_height

    def process_image(self, image_path: str, output_dir: str, prefix_num: int) -> List[str]:
        """
        Process a single image: resize and split if necessary.
        
        Args:
            image_path (str): Path to the input image
            output_dir (str): Directory to save processed images
            prefix_num (int): Prefix number for output files (3 digits)
            
        Returns:
            List[str]: List of paths to the generated images
        """
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        generated_files = []
        with Image.open(image_path) as img:
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            aspect_ratio = img.width / img.height
            new_height = int(self.target_width / aspect_ratio)
            resized_img = img.resize((self.target_width, new_height), Image.Resampling.LANCZOS)
            num_slices = math.ceil(new_height / self.target_height)
            for i in range(num_slices):
                start_y = i * self.target_height
                end_y = min(start_y + self.target_height, new_height)
                slice_img = resized_img.crop((0, start_y, self.target_width, end_y))
                # Now prefix is incremented for each output file
                output_filename = f"{prefix_num + i:03d}_{base_name}.png"
                output_path = os.path.join(output_dir, output_filename)
                slice_img.save(output_path, "PNG")
                generated_files.append(output_path)
        return generated_files

    def process_image_list(self, image_list: List[str], output_dir: str) -> List[str]:
        """
        Process multiple images from a list of file paths.
        
        Args:
            image_list (List[str]): List of paths to input images
            output_dir (str): Directory to save processed images
            
        Returns:
            List[str]: List of all generated image paths
        """
        all_generated_files = []
        prefix_counter = 1
        for image_path in image_list:
            generated_files = self.process_image(image_path, output_dir, prefix_counter)
            all_generated_files.extend(generated_files)
            prefix_counter += len(generated_files)
        return all_generated_files

    def process_directory(self, input_dir: str, output_dir: str, 
                        file_types: tuple = ('.jpg', '.jpeg', '.png')) -> List[str]:
        """
        Process all images in a directory.
        
        Args:
            input_dir (str): Directory containing input images
            output_dir (str): Directory to save processed images
            file_types (tuple): Tuple of accepted file extensions
            
        Returns:
            List[str]: List of all generated image paths
        """
        # Get all image files from directory
        image_files = []
        for filename in sorted(os.listdir(input_dir)):
            if filename.lower().endswith(file_types):
                image_files.append(os.path.join(input_dir, filename))
                
        return self.process_image_list(image_files, output_dir)
