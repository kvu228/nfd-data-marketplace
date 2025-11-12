"""
LSB Watermark Embedding Module

This module provides functions to embed watermarks into images using LSB technique.
"""

import numpy as np
from PIL import Image
from typing import Dict, List, Optional, Tuple


def select_pixels(image_shape: Tuple[int, int], carrier: np.ndarray, 
                  num_pixels: int) -> np.ndarray:
    """
    Select pixels based on carrier (pseudo-random but deterministic).
    
    Args:
        image_shape: (height, width) of the image
        carrier: Carrier pattern (used as seed for pixel selection)
        num_pixels: Number of pixels to select
    
    Returns:
        Array of shape (num_pixels, 2) with (row, col) coordinates
    """
    height, width = image_shape
    total_pixels = height * width
    
    # Convert carrier to seed (deterministic)
    if isinstance(carrier, (int, np.integer)):
        seed = int(carrier)
    else:
        # Hash the carrier array to get a seed
        seed = int(np.sum(np.abs(carrier)) * 1e6) % (2**31 - 1)
    
    # Create random state with seed
    rng = np.random.RandomState(seed)
    
    # Ensure we don't select more pixels than available
    num_pixels = min(num_pixels, total_pixels)
    
    # Generate random pixel indices
    pixel_indices = rng.choice(total_pixels, size=num_pixels, replace=False)
    
    # Convert to (row, col) coordinates
    rows = pixel_indices // width
    cols = pixel_indices % width
    
    positions = np.stack([rows, cols], axis=1)
    
    return positions


def embed_bits(pixel_array: np.ndarray, positions: np.ndarray, 
               bits: np.ndarray, channels: List[int]) -> np.ndarray:
    """
    Embed bits into LSB of selected pixels.
    
    Args:
        pixel_array: Image array (H, W, C)
        positions: Array of (row, col) coordinates (N, 2)
        bits: Binary array to embed (N,)
        channels: List of channel indices to use for embedding
    
    Returns:
        Modified pixel array
    """
    result = pixel_array.copy()
    
    num_positions = len(positions)
    num_bits = len(bits)
    num_channels = len(channels)
    
    # Calculate how to distribute bits across positions and channels
    total_capacity = num_positions * num_channels
    
    if num_bits > total_capacity:
        raise ValueError(
            f"Not enough capacity: need {num_bits} bits but only have "
            f"{total_capacity} capacity ({num_positions} pixels × {num_channels} channels)"
        )
    
    bit_idx = 0
    for pos_idx in range(num_positions):
        if bit_idx >= num_bits:
            break
            
        row, col = positions[pos_idx]
        
        for channel in channels:
            if bit_idx >= num_bits:
                break
            
            # Get current pixel value
            pixel_val = result[row, col, channel]
            
            # Clear LSB
            pixel_val = (pixel_val & 0xFE)
            
            # Set LSB to bit value
            pixel_val = pixel_val | int(bits[bit_idx])
            
            # Update pixel
            result[row, col, channel] = pixel_val
            
            bit_idx += 1
    
    return result


def compute_psnr(original: np.ndarray, watermarked: np.ndarray) -> float:
    """
    Compute PSNR between two images.
    
    Args:
        original: Original image array
        watermarked: Watermarked image array
    
    Returns:
        PSNR value in dB
    """
    mse = np.mean((original.astype(float) - watermarked.astype(float)) ** 2)
    
    if mse == 0:
        return float('inf')
    
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    
    return psnr


def embed_0bit(image: Image.Image, carrier: np.ndarray, 
               params: Optional[Dict] = None) -> Image.Image:
    """
    Embed 0-bit watermark (detection only) using LSB.
    
    The watermark is embedded by modifying LSBs of selected pixels according to
    a specific pattern. This pattern can be detected but doesn't carry a message.
    
    Args:
        image: Input PIL Image (RGB)
        carrier: Carrier pattern (used as seed for pixel selection)
        params: Dict with optional parameters:
            - num_pixels: Number of pixels to modify (default: 1000)
            - channels: List of channels to embed (default: [0,1,2] = RGB)
            - pattern: Pattern value to detect (default: alternating 0,1,0,1...)
    
    Returns:
        Watermarked PIL Image
    """
    if params is None:
        params = {}
    
    # Default parameters
    num_pixels = params.get('num_pixels', 1000)
    channels = params.get('channels', [0, 1, 2])
    pattern_type = params.get('pattern', 'alternating')
    
    # Convert image to numpy array
    img_array = np.array(image)
    
    # Ensure image is RGB
    if len(img_array.shape) == 2:
        img_array = np.stack([img_array] * 3, axis=2)
    elif img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]
    
    height, width, _ = img_array.shape
    
    # Select pixels
    positions = select_pixels((height, width), carrier, num_pixels)
    
    # Generate pattern bits
    total_bits_needed = len(positions) * len(channels)
    
    if pattern_type == 'alternating':
        # Alternating 0,1,0,1...
        pattern_bits = np.array([i % 2 for i in range(total_bits_needed)], dtype=np.uint8)
    elif pattern_type == 'ones':
        # All ones
        pattern_bits = np.ones(total_bits_needed, dtype=np.uint8)
    elif pattern_type == 'checksum':
        # Use carrier checksum pattern
        seed = int(np.sum(np.abs(carrier)) * 1e6) % 256
        rng = np.random.RandomState(seed)
        pattern_bits = rng.randint(0, 2, size=total_bits_needed, dtype=np.uint8)
    else:
        raise ValueError(f"Unknown pattern type: {pattern_type}")
    
    # Embed pattern bits
    watermarked_array = embed_bits(img_array, positions, pattern_bits, channels)
    
    # Convert back to PIL Image
    watermarked_image = Image.fromarray(watermarked_array.astype(np.uint8))
    
    return watermarked_image


def embed_multibit(image: Image.Image, message: np.ndarray, 
                   carrier: np.ndarray, params: Optional[Dict] = None) -> Image.Image:
    """
    Embed multi-bit message using LSB.
    
    The message bits are embedded into LSBs of pixels selected based on the carrier.
    Redundancy can be used to improve robustness.
    
    Args:
        image: Input PIL Image
        message: Boolean array [K] - message bits
        carrier: Carrier vectors (K,) - used for pixel selection
        params: Dict with optional parameters:
            - num_bits: K (message length)
            - redundancy: Number of times to repeat each bit (default: 3)
            - channels: Channels to embed (default: [0,1,2])
            - capacity: Bits per pixel (1-3, determined by len(channels))
    
    Returns:
        Watermarked PIL Image
    """
    if params is None:
        params = {}
    
    # Default parameters
    redundancy = params.get('redundancy', 3)
    channels = params.get('channels', [0, 1, 2])
    
    # Convert message to binary array
    message_bits = np.array(message, dtype=np.uint8)
    num_bits = len(message_bits)
    
    # Create redundant message
    redundant_bits = np.repeat(message_bits, redundancy)
    total_bits = len(redundant_bits)
    
    # Convert image to numpy array
    img_array = np.array(image)
    
    # Ensure image is RGB
    if len(img_array.shape) == 2:
        img_array = np.stack([img_array] * 3, axis=2)
    elif img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]
    
    height, width, _ = img_array.shape
    
    # Calculate number of pixels needed
    bits_per_pixel = len(channels)
    num_pixels_needed = int(np.ceil(total_bits / bits_per_pixel))
    
    # Check capacity
    total_pixels = height * width
    if num_pixels_needed > total_pixels:
        raise ValueError(
            f"Image too small: need {num_pixels_needed} pixels but only have {total_pixels}. "
            f"Reduce message length or redundancy."
        )
    
    # Select pixels based on carrier
    positions = select_pixels((height, width), carrier, num_pixels_needed)
    
    # Embed message bits
    watermarked_array = embed_bits(img_array, positions, redundant_bits, channels)
    
    # Convert back to PIL Image
    watermarked_image = Image.fromarray(watermarked_array.astype(np.uint8))
    
    # Compute and optionally report PSNR
    psnr = compute_psnr(img_array, watermarked_array)
    if params.get('verbose', False):
        print(f"PSNR: {psnr:.2f} dB")
    
    return watermarked_image

