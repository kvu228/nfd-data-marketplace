"""
Basic Demo of LSB Watermarking

This script demonstrates basic usage of lsb_wm package for both
0-bit (detection) and multi-bit (message) watermarking.

Usage:
    python demo_basic.py <image_path>
    
Example:
    python demo_basic.py ../input/sample.png
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from PIL import Image
from lsb_wm import embed_0bit, detect_0bit, embed_multibit, extract_multibit
from lsb_wm.encode import compute_psnr


def load_image(image_path):
    """Load and validate image from path."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    try:
        img = Image.open(image_path)
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img
    except Exception as e:
        raise ValueError(f"Failed to load image: {e}")


def demo_0bit_watermarking(image_path):
    """Demonstrate 0-bit watermarking (detection only)."""
    print("=" * 70)
    print("DEMO 1: 0-bit Watermarking (Detection Only)")
    print("=" * 70)
    
    # Load image
    print(f"Loading image: {image_path}")
    img = load_image(image_path)
    print(f"✓ Loaded image: {img.size}, mode: {img.mode}")
    
    # Define carrier
    carrier = np.array([12345])
    print(f"✓ Carrier seed: {carrier[0]}")
    
    # Embedding parameters
    params = {
        'num_pixels': 1000,
        'pattern': 'checksum',
        'channels': [0, 1, 2]
    }
    print(f"✓ Embedding {params['num_pixels']} pixels with pattern '{params['pattern']}'")
    
    # Embed watermark
    watermarked = embed_0bit(img, carrier, params)
    print(f"✓ Watermark embedded successfully")
    
    # Compute PSNR
    img_array = np.array(img)
    wm_array = np.array(watermarked)
    psnr = compute_psnr(img_array, wm_array)
    print(f"✓ PSNR: {psnr:.2f} dB (higher is better, >40 is excellent)")
    
    # Save watermarked image
    os.makedirs('../output', exist_ok=True)
    watermarked.save('../output/demo_0bit_watermarked.png')
    print(f"✓ Saved watermarked image to output/demo_0bit_watermarked.png")
    
    # Detect watermark
    print("\n--- Detection Phase ---")
    result = detect_0bit(watermarked, carrier, params)
    print(f"✓ Watermark detected: {result['detected']}")
    print(f"✓ Confidence: {result['confidence']:.4f}")
    print(f"✓ Pattern match: {result['pattern_match']:.4f}")
    
    # Test with wrong carrier (should not detect)
    print("\n--- Testing with wrong carrier ---")
    wrong_carrier = np.array([99999])
    result_wrong = detect_0bit(watermarked, wrong_carrier, params)
    print(f"✓ Watermark detected: {result_wrong['detected']}")
    print(f"✓ Confidence: {result_wrong['confidence']:.4f}")
    
    # Test on original (should not detect)
    print("\n--- Testing on original image (no watermark) ---")
    result_original = detect_0bit(img, carrier, params)
    print(f"✓ Watermark detected: {result_original['detected']}")
    print(f"✓ Confidence: {result_original['confidence']:.4f}")
    
    print("\n✅ 0-bit watermarking demo completed!\n")


def demo_multibit_watermarking(image_path):
    """Demonstrate multi-bit watermarking (message encoding)."""
    print("=" * 70)
    print("DEMO 2: Multi-bit Watermarking (Message Encoding)")
    print("=" * 70)
    
    # Load image
    print(f"Loading image: {image_path}")
    img = load_image(image_path)
    print(f"✓ Loaded image: {img.size}, mode: {img.mode}")
    
    # Create a message (e.g., 30 bits representing user IDs)
    # In practice, this could be user_ID (15 bits) + buyer_ID (15 bits)
    message = np.array([
        1, 0, 1, 1, 0, 0, 1, 0, 1, 1,  # First 10 bits
        0, 1, 0, 0, 1, 1, 1, 0, 0, 1,  # Next 10 bits
        0, 1, 1, 0, 1, 0, 0, 1, 1, 0   # Last 10 bits
    ], dtype=np.uint8)
    print(f"✓ Message length: {len(message)} bits")
    print(f"✓ Message: {message[:10]}... (showing first 10 bits)")
    
    # Define carrier
    carrier = np.array([42])
    print(f"✓ Carrier seed: {carrier[0]}")
    
    # Embedding parameters
    params_embed = {
        'num_bits': len(message),
        'redundancy': 3,  # Each bit repeated 3 times
        'channels': [0, 1, 2],
        'verbose': False
    }
    print(f"✓ Redundancy: {params_embed['redundancy']}x (for error correction)")
    
    # Embed message
    watermarked = embed_multibit(img, message, carrier, params_embed)
    print(f"✓ Message embedded successfully")
    
    # Compute PSNR
    img_array = np.array(img)
    wm_array = np.array(watermarked)
    psnr = compute_psnr(img_array, wm_array)
    print(f"✓ PSNR: {psnr:.2f} dB")
    
    # Save watermarked image
    os.makedirs('../output', exist_ok=True)
    watermarked.save('../output/demo_multibit_watermarked.png')
    print(f"✓ Saved watermarked image to output/demo_multibit_watermarked.png")
    
    # Extract message
    print("\n--- Extraction Phase ---")
    params_extract = {
        'num_bits': len(message),
        'redundancy': 3,
        'channels': [0, 1, 2]
    }
    decoded_message = extract_multibit(watermarked, carrier, params_extract)
    print(f"✓ Message extracted successfully")
    print(f"✓ Decoded message: {decoded_message[:10]}... (showing first 10 bits)")
    
    # Compute accuracy
    accuracy = np.sum(decoded_message == message) / len(message)
    bit_errors = np.sum(decoded_message != message)
    print(f"✓ Bit accuracy: {accuracy * 100:.2f}%")
    print(f"✓ Bit errors: {bit_errors} / {len(message)}")
    
    # Show comparison
    if bit_errors > 0:
        print("\n--- Bit differences ---")
        for i, (orig, dec) in enumerate(zip(message, decoded_message)):
            if orig != dec:
                print(f"  Bit {i}: original={orig}, decoded={dec}")
    else:
        print("\n✅ Perfect recovery! All bits match.")
    
    print("\n✅ Multi-bit watermarking demo completed!\n")


def create_sample_image_if_needed():
    """Create a sample image if no image is provided."""
    print("No image path provided. Creating a sample image...")
    
    # Create sample image with gradient
    size = (256, 256)
    img_array = np.zeros((size[0], size[1], 3), dtype=np.uint8)
    
    # Create a gradient pattern
    for i in range(size[0]):
        for j in range(size[1]):
            img_array[i, j, 0] = min(255, int(100 + (i / size[0]) * 50))
            img_array[i, j, 1] = min(255, int(150 + (j / size[1]) * 50))
            img_array[i, j, 2] = min(255, int(200 + ((i + j) / (size[0] + size[1])) * 50))
    
    img = Image.fromarray(img_array)
    
    # Save sample image
    os.makedirs('../input', exist_ok=True)
    sample_path = '../input/sample_generated.png'
    img.save(sample_path)
    print(f"✓ Sample image created and saved to: {sample_path}")
    
    return sample_path


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("LSB Watermarking Demo".center(70))
    print("=" * 70 + "\n")
    
    # Get image path from command line or create sample
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"Using provided image: {image_path}\n")
    else:
        print("Usage: python demo_basic.py <image_path>")
        print("Example: python demo_basic.py ../input/sample.png\n")
        image_path = create_sample_image_if_needed()
        print()
    
    try:
        # Verify image exists and is valid
        img_test = load_image(image_path)
        print(f"✓ Image validated: {img_test.size}, mode: {img_test.mode}\n")
        
        # Demo 1: 0-bit watermarking
        demo_0bit_watermarking(image_path)
        
        # Demo 2: Multi-bit watermarking
        demo_multibit_watermarking(image_path)
        
        print("=" * 70)
        print("All demos completed successfully!".center(70))
        print("=" * 70)
        print(f"\nOutput images saved to: ../output/")
        print("  - demo_0bit_watermarked.png")
        print("  - demo_multibit_watermarked.png")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("Please provide a valid image path.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

