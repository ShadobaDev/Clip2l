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

    def process_image(self, image_path: str, output_dir: str, start_postfix: int) -> Tuple[List[str], int]:
        """
        Process a single image: resize and split if necessary.
        
        Args:
            image_path (str): Path to the input image
            output_dir (str): Directory to save processed images
            start_postfix (int): Starting postfix number for output files

        Returns:
            Tuple[List[str], int]: (generated file paths, next postfix number)
        """
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        generated_files = []
        with Image.open(image_path) as img:
            # Normalize image to RGB while preserving transparency where present.
            # Handles modes like 'RGBA', 'LA', and palette 'P' correctly.
            if img.mode in ("RGBA", "LA") or (hasattr(img, "getbands") and 'A' in img.getbands()):
                # Convert to RGBA and composite on white background to remove alpha
                rgba = img.convert('RGBA')
                background = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
                background.paste(rgba, mask=rgba.split()[3])
                img = background.convert('RGB')
            elif img.mode == 'P':
                # Paletted images -> convert to RGBA first to preserve transparency if any
                rgba = img.convert('RGBA')
                background = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
                background.paste(rgba, mask=rgba.split()[3])
                img = background.convert('RGB')
            else:
                img = img.convert('RGB')

            aspect_ratio = img.width / img.height
            new_height = int(self.target_width / aspect_ratio)
            resized_img = img.resize((self.target_width, new_height), Image.Resampling.LANCZOS)
            num_slices = math.ceil(new_height / self.target_height)
            for i in range(num_slices):
                start_y = i * self.target_height
                end_y = min(start_y + self.target_height, new_height)
                slice_img = resized_img.crop((0, start_y, self.target_width, end_y))
                # Use a postfix (suffix) for numbering and increment for each output file
                postfix = start_postfix + i
                output_filename = f"{base_name}_{postfix:03d}.png"
                output_path = os.path.join(output_dir, output_filename)
                slice_img.save(output_path, "PNG")
                generated_files.append(output_path)
        # Return generated file paths and the next postfix to use
        next_postfix = start_postfix + len(generated_files)
        return generated_files, next_postfix

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
        postfix_counter = 1
        for image_path in image_list:
            generated_files, postfix_counter = self.process_image(image_path, output_dir, postfix_counter)
            all_generated_files.extend(generated_files)
        return all_generated_files

    def process_sequence_list(self, image_list: List[str], output_dir: str, start_postfix: int = 1) -> List[str]:
        """
        Process a sequence of images by concatenating them vertically and slicing across
        image boundaries. This produces output images of `target_width` x `target_height`
        that may contain parts of two adjacent source images when slices cross seams.

        Args:
            image_list (List[str]): Ordered list of image paths to concatenate
            output_dir (str): Directory to save processed images
            start_postfix (int): Starting postfix number for output files

        Returns:
            List[str]: List of generated file paths
        """
        os.makedirs(output_dir, exist_ok=True)

        # Open, normalize and resize each image to target_width preserving aspect ratio
        prepared_images = []
        heights = []
        for path in image_list:
            with Image.open(path) as im:
                # reuse normalization logic
                if im.mode in ("RGBA", "LA") or (hasattr(im, "getbands") and 'A' in im.getbands()):
                    rgba = im.convert('RGBA')
                    background = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
                    background.paste(rgba, mask=rgba.split()[3])
                    im_rgb = background.convert('RGB')
                elif im.mode == 'P':
                    rgba = im.convert('RGBA')
                    background = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
                    background.paste(rgba, mask=rgba.split()[3])
                    im_rgb = background.convert('RGB')
                else:
                    im_rgb = im.convert('RGB')

                aspect_ratio = im_rgb.width / im_rgb.height
                new_height = int(self.target_width / aspect_ratio)
                resized = im_rgb.resize((self.target_width, new_height), Image.Resampling.LANCZOS)
                prepared_images.append(resized)
                heights.append(resized.height)

        # Create a single tall image by pasting each prepared image vertically
        total_height = sum(heights)
        if total_height == 0:
            return []

        concat = Image.new('RGB', (self.target_width, total_height), (255, 255, 255))
        y = 0
        for im in prepared_images:
            concat.paste(im, (0, y))
            y += im.height

        # Slice the concatenated image into target_height strips
        generated_files = []
        num_slices = math.ceil(total_height / self.target_height)
        for i in range(num_slices):
            start_y = i * self.target_height
            end_y = min(start_y + self.target_height, total_height)
            slice_img = concat.crop((0, start_y, self.target_width, end_y))
            postfix = start_postfix + i
            # zero-padded postfix
            output_filename = f"{postfix:03d}.png"
            # use sequence naming: seq_<postfix> to avoid colliding with per-image naming
            output_filename = f"seq_{postfix:03d}.png"
            output_path = os.path.join(output_dir, output_filename)
            slice_img.save(output_path, "PNG")
            generated_files.append(output_path)

        return generated_files

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
