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

    def image_convert(self, img: Image.Image, color_space: str = 'RGB', convert: bool = True) -> Image.Image:
        """
        Convert or normalize an image to a target color space.

        Args:
            img (PIL.Image.Image): Opened image instance.
            color_space (str): Target color space name (e.g. 'RGB', 'RGBA', 'LA').
            convert (bool): If False, returns a copy without converting.

        Returns:
            PIL.Image.Image: Converted image.
        """
        if not convert:
            return img.copy()

        # Target RGB: composite alpha/palette onto white background for stable output
        if color_space.upper() == 'RGB':
            if img.mode in ("RGBA", "LA") or (hasattr(img, "getbands") and 'A' in img.getbands()):
                rgba = img.convert('RGBA')
                background = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
                background.paste(rgba, mask=rgba.split()[3])
                return background.convert('RGB')
            if img.mode == 'P':
                rgba = img.convert('RGBA')
                background = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
                background.paste(rgba, mask=rgba.split()[3])
                return background.convert('RGB')
            return img.convert('RGB')

        # Other explicit conversions
        return img.convert(color_space)

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
            # Normalize/convert input image
            img = self.image_convert(img, 'RGB', convert=True)

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

        # Process images one by one and stream output slices. We never hold more than
        # the "carry" buffer plus the current image in memory.
        prepared_iter = []
        # We'll iterate through files and process immediately
        generated_files = []
        carry = None  # Image.Image or None, holds leftover piece smaller than target_height
        postfix = start_postfix

        def flush_carry_slices(carry_img, postfix_start):
            """Yield (slice_img, postfix) for all full-size slices from carry_img."""
            out = []
            while carry_img is not None and carry_img.height >= self.target_height:
                slice_img = carry_img.crop((0, 0, self.target_width, self.target_height))
                out.append((slice_img, postfix_start))
                postfix_start += 1
                if carry_img.height == self.target_height:
                    carry_img = None
                else:
                    carry_img = carry_img.crop((0, self.target_height, self.target_width, carry_img.height))
            return out, carry_img, postfix_start

        for path in image_list:
            with Image.open(path) as im:
                im_rgb = self.image_convert(im, 'RGB', convert=True)
                aspect_ratio = im_rgb.width / im_rgb.height
                new_height = int(self.target_width / aspect_ratio)
                cur = im_rgb.resize((self.target_width, new_height), Image.Resampling.LANCZOS)

                # If there's no carry, set cur as carry and flush full slices
                if carry is None:
                    carry = cur
                    out_slices, carry, postfix = flush_carry_slices(carry, postfix)
                    for s, p in out_slices:
                        out_name = f"seq_{p:03d}.png"
                        out_path = os.path.join(output_dir, out_name)
                        s.save(out_path, 'PNG')
                        generated_files.append(out_path)
                    continue

                # There is leftover (carry.height < target_height). Fill from cur
                while carry is not None and carry.height < self.target_height and cur.height > 0:
                    need = self.target_height - carry.height
                    take_h = min(need, cur.height)
                    top_piece = cur.crop((0, 0, self.target_width, take_h))
                    # create combined slice
                    combined = Image.new('RGB', (self.target_width, carry.height + take_h), (255, 255, 255))
                    combined.paste(carry, (0, 0))
                    combined.paste(top_piece, (0, carry.height))
                    out_name = f"seq_{postfix:03d}.png"
                    out_path = os.path.join(output_dir, out_name)
                    combined.save(out_path, 'PNG')
                    generated_files.append(out_path)
                    postfix += 1

                    # advance cur by take_h
                    if take_h == cur.height:
                        cur = None
                        carry = None
                        break
                    else:
                        cur = cur.crop((0, take_h, self.target_width, cur.height))
                        # now cur may still have full slices; set carry to None and flush cur
                        carry = None

                # If cur still exists, flush full target_height slices from it
                if cur is not None:
                    out_slices, carry, postfix = flush_carry_slices(cur, postfix)
                    for s, p in out_slices:
                        out_name = f"seq_{p:03d}.png"
                        out_path = os.path.join(output_dir, out_name)
                        s.save(out_path, 'PNG')
                        generated_files.append(out_path)
                    # any remaining piece from cur becomes the new carry
                    # flush_carry_slices returned residual in carry variable

        # After all images processed, if carry remains (shorter than target), output it
        if carry is not None and carry.height > 0:
            out_name = f"seq_{postfix:03d}.png"
            out_path = os.path.join(output_dir, out_name)
            carry.save(out_path, 'PNG')
            generated_files.append(out_path)

        return generated_files

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
