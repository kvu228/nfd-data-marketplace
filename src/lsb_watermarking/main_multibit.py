"""
LSB Watermarking - Main Module
Interface tương tự SSL watermarking nhưng sử dụng thuật toán LSB
"""
import os
from os import path, remove
from shutil import move
from tempfile import NamedTemporaryFile
from glob import glob
from os.path import join
import numpy as np

from lsb_watermarking import encode
from lsb_watermarking import decode
from lsb_watermarking import utils


class Watermark:
    """
    LSB Watermarking class với interface tương tự SSL watermarking
    """

    def __init__(self) -> None:
        self.base_dir = join(os.getcwd(), 'src')
        self.data_dir = join(self.base_dir, "lsb_watermarking", "input")
        self.output_dir = join(self.base_dir, "lsb_watermarking", "output", "imgs")
        self.save_images = True
        self.decode_only = False
        self.verbose = 1

        self.msg_type = "bit"
        self.msg_path = None
        self.num_bits = 12  # 6 bits for owner_id + 6 bits for buyer_id

        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def remove_dir_contents(self, dir: str):
        """Remove all files in directory"""
        if not os.path.exists(dir):
            return
        
        files = glob(join(dir, "*"))
        for f in files:
            if os.path.isfile(f):
                remove(f)

    def decode_watermark(self):
        """
        Decode watermark from images in data_dir
        
        Returns:
            List of decoded watermark strings (binary)
        """
        if self.verbose > 0:
            print('>>> Decoding watermarks...')
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
        
        # Get all images in data_dir
        image_paths = []
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    image_paths.append(os.path.join(root, file))
        
        if not image_paths:
            if self.verbose > 0:
                print('>>> No images found in data directory')
            return []
        
        # Decode watermarks
        decoded_messages = decode.lsb_decode_batch(image_paths, self.num_bits)
        
        # Convert to binary strings
        watermark_strings = []
        for msg in decoded_messages:
            watermark_str = ''.join(map(str, msg.astype(int).tolist()))
            watermark_strings.append(watermark_str)
        
        return watermark_strings

    def watermark(self):
        """
        Watermark images in data_dir with messages from msg_path
        """
        # Load images
        if self.verbose > 0:
            print('>>> Loading images from %s...' % self.data_dir)
        
        image_paths = []
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    image_paths.append(os.path.join(root, file))
        
        if not image_paths:
            if self.verbose > 0:
                print('>>> No images found in data directory')
            return
        
        num_images = len(image_paths)
        
        # Load messages
        if self.verbose > 0:
            print('>>> Loading messages...')
        
        if self.msg_path is None:
            msgs = utils.generate_messages(num_images, self.num_bits)
        else:
            if not os.path.exists(self.msg_path):
                if self.verbose > 0:
                    print('Generating random messages into %s...' % self.msg_path)
                os.makedirs(os.path.dirname(self.msg_path) if os.path.dirname(self.msg_path) else '.', exist_ok=True)
                msgs = utils.generate_messages(num_images, self.num_bits)
                utils.save_messages(msgs, self.msg_path)
            else:
                if self.verbose > 0:
                    print('Loading %s messages from %s...' % (self.msg_type, self.msg_path))
                msgs = utils.load_messages(self.msg_path, self.msg_type, num_images)
        
        # Ensure we have enough messages
        if len(msgs) < num_images:
            # Repeat messages if needed
            msgs = np.tile(msgs, (num_images // len(msgs) + 1, 1))[:num_images]
        
        # Watermark images
        if self.verbose > 0:
            print('>>> Marking images with LSB...')
        
        # Create output directory
        imgs_dir = os.path.join(self.output_dir, 'imgs')
        os.makedirs(imgs_dir, exist_ok=True)
        
        # Encode watermarks
        output_paths = encode.lsb_encode_batch(image_paths, msgs, imgs_dir)
        
        if self.verbose > 0:
            print('>>> Saving images into %s...' % imgs_dir)
            print('>>> Watermarked %d images' % len(output_paths))

    def extract_watermark(self, img_filepath: str):
        """
        Extract watermark from a single image
        
        Args:
            img_filepath: Path to watermarked image
        
        Returns:
            Tuple of (owner_id, buyer_id)
        """
        # Create subdirectory in data_dir
        subdir = join(self.data_dir, "0")
        os.makedirs(subdir, exist_ok=True)
        self.remove_dir_contents(subdir)
        
        base = path.basename(img_filepath)
        new_path = path.join(subdir, base)
        
        # Copy image to data_dir
        move(img_filepath, new_path)
        
        # Decode watermark
        wm = self.decode_watermark()
        
        # Move image back
        move(new_path, img_filepath)
        
        if not wm:
            raise ValueError("Failed to decode watermark")
        
        if self.verbose > 0:
            print("decode watermark: %s" % wm[0])
        
        # Parse watermark string
        wm_str = wm[0]  # Get the first decoded watermark string
        
        if len(wm_str) < 12:
            raise ValueError(f"Watermark too short: {len(wm_str)} bits, expected 12")
        
        # Extract owner_id (6 bits) and buyer_id (6 bits)
        oid = int(wm_str[:6], 2)
        bid = int(wm_str[6:12], 2)
        
        return oid, bid

    def set_watermark(self, owner_id: int, buyer_id: int):
        """
        Set watermark message from owner_id and buyer_id
        
        Args:
            owner_id: Owner ID (will be encoded as 6 bits)
            buyer_id: Buyer ID (will be encoded as 6 bits)
        """
        t = NamedTemporaryFile("w", delete=False)
        
        # Convert to binary
        owner_bin = bin(owner_id)[2:]
        buyer_bin = bin(buyer_id)[2:]
        
        # Pad to 8 bits, then take last 6 bits
        owner_bin = owner_bin.zfill(8)
        buyer_bin = buyer_bin.zfill(8)
        
        # Combine: 6 bits owner + 6 bits buyer = 12 bits total
        watermark_bin = owner_bin[2:] + buyer_bin[2:]
        
        if self.verbose > 0:
            print("encoded watermark: %s" % watermark_bin)
        
        t.write(watermark_bin)
        t.close()
        
        self.msg_path = t.name

    def watermark_image(self, img_filepath: str):
        """
        Watermark a single image file
        
        Args:
            img_filepath: Path to image file to watermark
        """
        base = path.basename(img_filepath)
        subdir = join(self.data_dir, "0")
        os.makedirs(subdir, exist_ok=True)
        
        new_path = path.join(subdir, base)
        
        # Clear subdirectory
        self.remove_dir_contents(subdir)
        
        # Copy image to data_dir
        move(img_filepath, new_path)
        
        # Watermark
        self.watermark()
        
        # Move watermarked image back
        watermarked_path = path.join(self.output_dir, "imgs", base)
        if not os.path.exists(watermarked_path):
            # Try with different extension
            name, ext = os.path.splitext(base)
            watermarked_path = path.join(self.output_dir, "imgs", f"{name}_watermarked.png")
            if not os.path.exists(watermarked_path):
                # Get first file in output directory
                output_files = glob(join(self.output_dir, "imgs", "*"))
                if output_files:
                    watermarked_path = output_files[0]
                else:
                    raise FileNotFoundError("Watermarked image not found")
        
        # Remove original from data_dir
        if os.path.exists(new_path):
            remove(new_path)
        
        # Move watermarked image to original location
        move(watermarked_path, img_filepath)
        
        if self.verbose > 0:
            print('Watermarked image successfully!')

