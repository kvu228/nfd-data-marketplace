"""
Extract Watermark Only - Standalone Script

This script extracts watermarks from already watermarked images.
Use this when you have watermarked images and want to extract the embedded information.

Usage:
    python extract_only.py <watermarked_image_path> [options]
    
Examples:
    # Extract from multibit watermarked image
    python extract_only.py ../output/demo_multibit_watermarked.png --carrier 42 --num-bits 30
    
    # Detect 0-bit watermark
    python extract_only.py ../output/demo_0bit_watermarked.png --type 0bit --carrier 12345
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import numpy as np
from PIL import Image
from lsb_wm import detect_0bit, extract_multibit


def load_image(image_path):
    """Load and validate image from path."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img
    except Exception as e:
        raise ValueError(f"Failed to load image: {e}")


def extract_0bit(image_path, carrier_seed, num_pixels=1000, pattern='checksum'):
    """Extract and detect 0-bit watermark."""
    print("=" * 70)
    print("0-bit Watermark Detection")
    print("=" * 70)
    print(f"Image: {image_path}")
    print(f"Carrier seed: {carrier_seed}")
    print(f"Checking {num_pixels} pixels with pattern '{pattern}'")
    print()
    
    # Load image
    img = load_image(image_path)
    print(f"[OK] Loaded image: {img.size}, mode: {img.mode}")
    
    # Detect parameters
    carrier = np.array([carrier_seed])
    params = {
        'num_pixels': num_pixels,
        'pattern': pattern,
        'channels': [0, 1, 2],
        'threshold': 0.7
    }
    
    # Detect watermark
    print("\n--- Detection Results ---")
    result = detect_0bit(img, carrier, params)
    
    print(f"Watermark detected: {'[YES]' if result['detected'] else '[NO]'}")
    print(f"Confidence: {result['confidence']:.4f} ({result['confidence']*100:.2f}%)")
    print(f"Pattern match: {result['pattern_match']:.4f} ({result['pattern_match']*100:.2f}%)")
    
    if result['detected']:
        print("\n[SUCCESS] Watermark successfully detected!")
    else:
        print("\n[WARNING] No watermark detected (or wrong parameters)")
    
    return result


def extract_multibit(image_path, carrier_seed, num_bits, redundancy=3, 
                     decode_as_transaction=False):
    """Extract multi-bit watermark."""
    print("=" * 70)
    print("Multi-bit Watermark Extraction")
    print("=" * 70)
    print(f"Image: {image_path}")
    print(f"Carrier seed: {carrier_seed}")
    print(f"Message length: {num_bits} bits")
    print(f"Redundancy: {redundancy}x")
    print()
    
    # Load image
    img = load_image(image_path)
    print(f"[OK] Loaded image: {img.size}, mode: {img.mode}")
    
    # Extract parameters
    carrier = np.array([carrier_seed])
    params = {
        'num_bits': num_bits,
        'redundancy': redundancy,
        'channels': [0, 1, 2]
    }
    
    # Extract watermark
    print("\n--- Extraction Results ---")
    from lsb_wm import extract_multibit as extract_func
    decoded_message = extract_func(img, carrier, params)
    
    print(f"[OK] Watermark extracted successfully!")
    print(f"[OK] Extracted {len(decoded_message)} bits")
    print(f"\nMessage (binary): {''.join(map(str, decoded_message.astype(int)))}")
    print(f"Message (array):  {decoded_message}")
    
    # Decode as transaction if requested
    if decode_as_transaction and num_bits == 30:
        print("\n--- Decoded as Transaction (15+15 bits) ---")
        owner_bits = decoded_message[:15]
        buyer_bits = decoded_message[15:30]
        
        owner_id = int(''.join(map(str, owner_bits.astype(int))), 2)
        buyer_id = int(''.join(map(str, buyer_bits.astype(int))), 2)
        
        print(f"Owner ID: {owner_id:5d} (binary: {''.join(map(str, owner_bits.astype(int)))})")
        print(f"Buyer ID: {buyer_id:5d} (binary: {''.join(map(str, buyer_bits.astype(int)))})")
        print(f"[TRANSACTION] User {owner_id} -> User {buyer_id}")
    
    print("\n[SUCCESS] Extraction completed!")
    
    return decoded_message


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract watermark from watermarked images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract multibit watermark (default)
  python extract_only.py ../output/demo_multibit_watermarked.png
  
  # Extract with custom parameters
  python extract_only.py image.png --carrier 12345 --num-bits 50 --redundancy 5
  
  # Detect 0-bit watermark
  python extract_only.py image.png --type 0bit --carrier 12345
  
  # Decode as transaction
  python extract_only.py image.png --decode-transaction
        """
    )
    
    parser.add_argument('image', help='Path to watermarked image')
    parser.add_argument('--type', choices=['0bit', 'multibit'], default='multibit',
                       help='Watermark type (default: multibit)')
    parser.add_argument('--carrier', type=int, default=42,
                       help='Carrier seed (default: 42)')
    parser.add_argument('--num-bits', type=int, default=30,
                       help='Message length in bits for multibit (default: 30)')
    parser.add_argument('--redundancy', type=int, default=3,
                       help='Redundancy factor for multibit (default: 3)')
    parser.add_argument('--num-pixels', type=int, default=1000,
                       help='Number of pixels for 0bit (default: 1000)')
    parser.add_argument('--pattern', default='checksum',
                       choices=['alternating', 'ones', 'checksum'],
                       help='Pattern type for 0bit (default: checksum)')
    parser.add_argument('--decode-transaction', action='store_true',
                       help='Decode as transaction (15+15 bits)')
    
    args = parser.parse_args()
    
    try:
        print("\n" + "=" * 70)
        print("LSB Watermark Extractor".center(70))
        print("=" * 70 + "\n")
        
        if args.type == '0bit':
            extract_0bit(args.image, args.carrier, args.num_pixels, args.pattern)
        else:
            extract_multibit(args.image, args.carrier, args.num_bits, 
                           args.redundancy, args.decode_transaction)
        
        print("\n" + "=" * 70)
        
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

