"""
LSB Watermark Extraction Module

This module provides functions to extract and detect watermarks from images.
"""

import numpy as np
from PIL import Image
from typing import Dict, List, Optional
from .encode import select_pixels


def extract_bits(pixel_array: np.ndarray, positions: np.ndarray, 
                 channels: List[int], num_bits: int) -> np.ndarray:
    """
    Extract bits from LSB of selected pixels.
    
    Args:
        pixel_array: Image array (H, W, C)
        positions: Array of (row, col) coordinates (N, 2)
        channels: List of channel indices to extract from
        num_bits: Number of bits to extract
    
    Returns:
        Binary array of extracted bits (num_bits,)
    """
    extracted_bits = []
    
    bit_idx = 0
    for pos_idx in range(len(positions)):
        if bit_idx >= num_bits:
            break
        
        row, col = positions[pos_idx]
        
        for channel in channels:
            if bit_idx >= num_bits:
                break
            
            # Get pixel value
            pixel_val = pixel_array[row, col, channel]
            
            # Extract LSB
            lsb = pixel_val & 1
            extracted_bits.append(lsb)
            
            bit_idx += 1
    
    return np.array(extracted_bits, dtype=np.uint8)


def majority_vote(bits_redundant: np.ndarray, redundancy: int) -> np.ndarray:
    """
    Apply majority voting for error correction.
    
    Args:
        bits_redundant: Redundant bits array (N*redundancy,)
        redundancy: Number of times each bit is repeated
    
    Returns:
        Decoded bits after majority voting (N,)
    """
    num_bits = len(bits_redundant) // redundancy
    decoded_bits = np.zeros(num_bits, dtype=np.uint8)
    
    for i in range(num_bits):
        # Get redundant copies of this bit
        start_idx = i * redundancy
        end_idx = start_idx + redundancy
        redundant_copies = bits_redundant[start_idx:end_idx]
        
        # Majority vote
        decoded_bits[i] = 1 if np.sum(redundant_copies) > (redundancy / 2) else 0
    
    return decoded_bits


def compute_bit_accuracy(decoded: np.ndarray, original: np.ndarray) -> float:
    """
    Compute bit accuracy between decoded and original messages.
    
    Args:
        decoded: Decoded message bits
        original: Original message bits
    
    Returns:
        Bit accuracy (0.0 to 1.0)
    """
    if len(decoded) != len(original):
        min_len = min(len(decoded), len(original))
        decoded = decoded[:min_len]
        original = original[:min_len]
    
    if len(decoded) == 0:
        return 0.0
    
    correct = np.sum(decoded == original)
    accuracy = correct / len(decoded)
    
    return accuracy


def detect_0bit(image: Image.Image, carrier: np.ndarray, 
                params: Optional[Dict] = None) -> Dict:
    """
    Detect 0-bit watermark from image.
    
    Extracts LSBs from selected pixels and checks for pattern matching.
    
    Args:
        image: PIL Image (potentially watermarked)
        carrier: Same carrier used in embedding
        params: Detection parameters:
            - num_pixels: Number of pixels to check (default: 1000)
            - channels: Channels to check (default: [0,1,2])
            - pattern: Expected pattern type (default: 'alternating')
            - threshold: Detection threshold (default: 0.7)
    
    Returns:
        Dict with:
            - detected: Boolean (watermark detected or not)
            - confidence: Float [0, 1] (confidence score)
            - pattern_match: Percentage of pattern matched
    """
    if params is None:
        params = {}
    
    # Default parameters
    num_pixels = params.get('num_pixels', 1000)
    channels = params.get('channels', [0, 1, 2])
    pattern_type = params.get('pattern', 'alternating')
    threshold = params.get('threshold', 0.7)
    
    # Convert image to numpy array
    img_array = np.array(image)
    
    # Ensure image is RGB
    if len(img_array.shape) == 2:
        img_array = np.stack([img_array] * 3, axis=2)
    elif img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]
    
    height, width, _ = img_array.shape
    
    # Select same pixels as embedding
    positions = select_pixels((height, width), carrier, num_pixels)
    
    # Extract bits
    total_bits = len(positions) * len(channels)
    extracted_bits = extract_bits(img_array, positions, channels, total_bits)
    
    # Generate expected pattern
    if pattern_type == 'alternating':
        expected_pattern = np.array([i % 2 for i in range(total_bits)], dtype=np.uint8)
    elif pattern_type == 'ones':
        expected_pattern = np.ones(total_bits, dtype=np.uint8)
    elif pattern_type == 'checksum':
        seed = int(np.sum(np.abs(carrier)) * 1e6) % 256
        rng = np.random.RandomState(seed)
        expected_pattern = rng.randint(0, 2, size=total_bits, dtype=np.uint8)
    else:
        raise ValueError(f"Unknown pattern type: {pattern_type}")
    
    # Compute pattern match
    matches = np.sum(extracted_bits == expected_pattern)
    pattern_match = matches / total_bits
    
    # Detection decision
    detected = pattern_match >= threshold
    confidence = pattern_match
    
    result = {
        'detected': bool(detected),
        'confidence': float(confidence),
        'pattern_match': float(pattern_match)
    }
    
    return result


def extract_multibit(image: Image.Image, carrier: np.ndarray, 
                     params: Optional[Dict] = None) -> np.ndarray:
    """
    Extract multi-bit message from image.
    
    Extracts LSBs from pixels and reconstructs the message using majority voting
    if redundancy was used during embedding.
    
    Args:
        image: PIL Image
        carrier: Carrier vectors (K,) - same as used in embedding
        params: Extraction parameters:
            - num_bits: K (message length)
            - redundancy: Redundancy factor (default: 3)
            - channels: Channels to extract from (default: [0,1,2])
    
    Returns:
        Boolean array [K] - decoded message
    """
    if params is None:
        params = {}
    
    # Default parameters
    num_bits = params.get('num_bits', None)
    redundancy = params.get('redundancy', 3)
    channels = params.get('channels', [0, 1, 2])
    
    if num_bits is None:
        raise ValueError("num_bits must be specified in params")
    
    # Convert image to numpy array
    img_array = np.array(image)
    
    # Ensure image is RGB
    if len(img_array.shape) == 2:
        img_array = np.stack([img_array] * 3, axis=2)
    elif img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]
    
    height, width, _ = img_array.shape
    
    # Calculate total bits to extract (with redundancy)
    total_bits = num_bits * redundancy
    
    # Calculate number of pixels needed
    bits_per_pixel = len(channels)
    num_pixels_needed = int(np.ceil(total_bits / bits_per_pixel))
    
    # Select same pixels as embedding
    positions = select_pixels((height, width), carrier, num_pixels_needed)
    
    # Extract redundant bits
    redundant_bits = extract_bits(img_array, positions, channels, total_bits)
    
    # Apply majority voting
    decoded_message = majority_vote(redundant_bits, redundancy)
    
    return decoded_message

