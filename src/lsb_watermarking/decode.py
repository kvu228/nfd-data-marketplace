"""
LSB Watermarking Decoding Module
"""
import numpy as np
from PIL import Image


def lsb_decode_image(image_path, num_bits):
    """
    Decode watermark bits from image using LSB (Least Significant Bit) method.
    
    Args:
        image_path: Path to the watermarked image
        num_bits: Number of bits to decode
    
    Returns:
        Array of decoded bits (0s and 1s)
    """
    # Load image
    img = Image.open(image_path)
    
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convert to numpy array
    img_array = np.array(img)
    height, width, channels = img_array.shape
    
    # Check capacity
    total_pixels = height * width * channels
    if num_bits > total_pixels:
        raise ValueError(f"Requested {num_bits} bits but image only has {total_pixels} pixels")
    
    # Flatten image array
    img_flat = img_array.flatten()
    
    # Extract LSBs
    watermark_bits = np.zeros(num_bits, dtype=np.uint8)
    for i in range(num_bits):
        watermark_bits[i] = img_flat[i] & 0x01
    
    return watermark_bits


def lsb_decode_batch(image_paths, num_bits):
    """
    Decode watermarks from multiple images.
    
    Args:
        image_paths: List of paths to watermarked images
        num_bits: Number of bits to decode from each image
    
    Returns:
        List of decoded watermark bit arrays
    """
    decoded_messages = []
    
    for img_path in image_paths:
        watermark_bits = lsb_decode_image(img_path, num_bits)
        decoded_messages.append(watermark_bits)
    
    return decoded_messages

