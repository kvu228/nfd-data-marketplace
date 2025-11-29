"""
LSB Watermarking Encoding Module
"""
import numpy as np
from PIL import Image
import os


def lsb_encode_image(image_path, watermark_bits, output_path=None):
    """
    Encode watermark bits into image using LSB (Least Significant Bit) method.
    
    Args:
        image_path: Path to the original image
        watermark_bits: List or array of bits (0s and 1s) to encode
        output_path: Path to save watermarked image (if None, overwrites original)
    
    Returns:
        Path to the watermarked image
    """
    # Load image
    img = Image.open(image_path)
    
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convert to numpy array
    img_array = np.array(img)
    height, width, channels = img_array.shape
    
    # Flatten watermark bits
    watermark_bits = np.array(watermark_bits, dtype=np.uint8).flatten()
    num_bits = len(watermark_bits)
    
    # Check if image has enough capacity
    total_pixels = height * width * channels
    if num_bits > total_pixels:
        raise ValueError(f"Image too small. Need at least {num_bits} pixels, got {total_pixels}")
    
    # Flatten image array
    img_flat = img_array.flatten()
    
    # Encode watermark bits into LSB
    for i in range(num_bits):
        # Clear LSB and set to watermark bit
        img_flat[i] = (img_flat[i] & 0xFE) | watermark_bits[i]
    
    # Reshape back to image dimensions
    img_array_watermarked = img_flat.reshape(height, width, channels)
    
    # Convert back to PIL Image
    img_watermarked = Image.fromarray(img_array_watermarked.astype(np.uint8), 'RGB')
    
    # Save watermarked image
    if output_path is None:
        output_path = image_path
    
    img_watermarked.save(output_path, format='PNG')
    
    return output_path


def lsb_encode_batch(image_paths, watermark_messages, output_dir=None):
    """
    Encode watermarks into multiple images.
    
    Args:
        image_paths: List of paths to images
        watermark_messages: List of watermark bit arrays (one per image)
        output_dir: Directory to save watermarked images (if None, overwrites originals)
    
    Returns:
        List of paths to watermarked images
    """
    output_paths = []
    
    for i, (img_path, watermark_bits) in enumerate(zip(image_paths, watermark_messages)):
        if output_dir:
            filename = os.path.basename(img_path)
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{name}_watermarked{ext}")
        else:
            output_path = None
        
        output_path = lsb_encode_image(img_path, watermark_bits, output_path)
        output_paths.append(output_path)
    
    return output_paths

