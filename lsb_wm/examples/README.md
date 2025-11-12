# LSB Watermarking Examples

This folder contains example scripts demonstrating how to use the LSB watermarking library.

## Available Scripts

### 1. demo_basic.py - Complete Demo

Full demonstration of all watermarking capabilities including embedding and extraction.

**Usage:**
```bash
# With your own image
python demo_basic.py /path/to/your/image.png

# Without arguments (auto-generates sample image)
python demo_basic.py
```

**Features:**
- Demo 1: 0-bit watermarking (detection only)
- Demo 2: Multi-bit watermarking (message encoding)
- Demo 3: Extract from saved file
- Automatic sample image generation
- Visual quality assessment (PSNR)
- Verification and accuracy reporting

**Output:**
- `../output/demo_0bit_watermarked.png` - 0-bit watermarked image
- `../output/demo_multibit_watermarked.png` - Multi-bit watermarked image

---

### 2. extract_only.py - Watermark Extraction Tool

Standalone tool for extracting watermarks from already watermarked images.

**Basic Usage:**
```bash
# Extract multi-bit watermark (default settings)
python extract_only.py ../output/demo_multibit_watermarked.png

# Detect 0-bit watermark
python extract_only.py ../output/demo_0bit_watermarked.png --type 0bit --carrier 12345
```

**Advanced Usage:**
```bash
# Extract with custom parameters
python extract_only.py image.png --carrier 42 --num-bits 30 --redundancy 3

# Decode as transaction (User IDs)
python extract_only.py image.png --decode-transaction

# Extract with different redundancy
python extract_only.py image.png --num-bits 50 --redundancy 5

# Detect 0-bit with custom pattern
python extract_only.py image.png --type 0bit --carrier 12345 --num-pixels 2000 --pattern alternating
```

**Command Line Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `image` | positional | required | Path to watermarked image |
| `--type` | choice | multibit | Watermark type: 0bit or multibit |
| `--carrier` | int | 42 | Carrier seed (must match embedding) |
| `--num-bits` | int | 30 | Message length for multibit |
| `--redundancy` | int | 3 | Redundancy factor for multibit |
| `--num-pixels` | int | 1000 | Number of pixels for 0bit |
| `--pattern` | choice | checksum | Pattern for 0bit: alternating/ones/checksum |
| `--decode-transaction` | flag | false | Decode as transaction (15+15 bits) |

**Examples:**

```bash
# Example 1: Basic extraction
python extract_only.py watermarked_nft.png

# Example 2: Extract and decode transaction
python extract_only.py watermarked_nft.png --decode-transaction

# Example 3: 0-bit detection
python extract_only.py watermarked_image.png --type 0bit --carrier 12345

# Example 4: Custom parameters
python extract_only.py custom.png --carrier 9999 --num-bits 60 --redundancy 5
```

---

## Quick Start Guide

### Step 1: Run Complete Demo

```bash
# Generate watermarked images
python demo_basic.py
```

This will create sample watermarked images in `../output/` folder.

### Step 2: Extract from Saved Images

```bash
# Extract multi-bit watermark
python extract_only.py ../output/demo_multibit_watermarked.png --decode-transaction

# Detect 0-bit watermark
python extract_only.py ../output/demo_0bit_watermarked.png --type 0bit --carrier 12345
```

---

## Expected Output

### Multi-bit Extraction Output

```
======================================================================
                       LSB Watermark Extractor                        
======================================================================

======================================================================
Multi-bit Watermark Extraction
======================================================================
Image: ../output/demo_multibit_watermarked.png
Carrier seed: 42
Message length: 30 bits
Redundancy: 3x

[OK] Loaded image: (642, 350), mode: RGB

--- Extraction Results ---
[OK] Watermark extracted successfully!
[OK] Extracted 30 bits

Message (binary): 101100101101001110010110100110
Message (array):  [1 0 1 1 0 0 1 0 1 1 0 1 0 0 1 1 1 0 0 1 0 1 1 0 1 0 0 1 1 0]

--- Decoded as Transaction (15+15 bits) ---
Owner ID: 22889 (binary: 101100101101001)
Buyer ID: 26022 (binary: 110010110100110)
[TRANSACTION] User 22889 -> User 26022

[SUCCESS] Extraction completed!

======================================================================
```

### 0-bit Detection Output

```
======================================================================
0-bit Watermark Detection
======================================================================
Image: ../output/demo_0bit_watermarked.png
Carrier seed: 12345
Checking 1000 pixels with pattern 'checksum'

[OK] Loaded image: (642, 350), mode: RGB

--- Detection Results ---
Watermark detected: [YES]
Confidence: 1.0000 (100.00%)
Pattern match: 1.0000 (100.00%)

[SUCCESS] Watermark successfully detected!
```

---

## Use Cases

### Use Case 1: NFT Ownership Tracking

```bash
# Embed transaction when NFT is sold
python demo_basic.py nft_artwork.png

# Later, verify ownership
python extract_only.py watermarked_nft.png --decode-transaction
# Output: [TRANSACTION] User 15 -> User 23
```

### Use Case 2: Copyright Detection

```bash
# Embed detection-only watermark
python demo_basic.py artwork.png

# Check if image has your watermark
python extract_only.py suspicious_image.png --type 0bit --carrier YOUR_SECRET_KEY
# Output: Watermark detected: [YES] or [NO]
```

### Use Case 3: Batch Processing

```bash
# Embed watermarks in multiple images
for img in input/*.png; do
    python demo_basic.py "$img"
done

# Extract from all watermarked images
for img in output/*_watermarked.png; do
    python extract_only.py "$img" --decode-transaction
done
```

---

## Tips & Troubleshooting

### Tip 1: Remember Your Carrier Seed!
The carrier seed is like a password. You MUST use the same carrier seed for extraction as you used for embedding.

```bash
# Embedding with carrier 12345
python demo_basic.py image.png --carrier 12345

# Must use same carrier for extraction
python extract_only.py watermarked.png --carrier 12345
```

### Tip 2: Match All Parameters
All extraction parameters must match the embedding parameters:
- `num_bits`
- `redundancy`
- `channels`
- `carrier`

### Tip 3: Save as PNG, Not JPEG
JPEG compression can damage watermarks. Always save watermarked images as PNG.

```python
watermarked.save('output.png')  # Good
watermarked.save('output.jpg')  # Bad - may lose watermark
```

### Tip 4: Check PSNR
Higher PSNR = better quality. Aim for >40 dB.

### Common Issues

**Issue**: "No watermark detected"
- ✓ Check carrier seed matches
- ✓ Check image hasn't been modified/compressed
- ✓ Verify correct pattern type for 0-bit

**Issue**: "Low bit accuracy"
- ✓ Increase redundancy
- ✓ Avoid JPEG compression
- ✓ Don't resize/crop watermarked image

**Issue**: "Image too small" error
- ✓ Reduce `num_bits`
- ✓ Reduce `redundancy`
- ✓ Use larger image

---

## API Usage in Python

If you want to use the functions directly in your code:

```python
from PIL import Image
import numpy as np
from lsb_wm import embed_multibit, extract_multibit

# Embed
img = Image.open('image.png')
message = np.array([1,0,1,1,0], dtype=np.uint8)
carrier = np.array([42])
params = {'num_bits': 5, 'redundancy': 3}

watermarked = embed_multibit(img, message, carrier, params)
watermarked.save('watermarked.png')

# Extract
decoded = extract_multibit(watermarked, carrier, params)
print(f"Decoded: {decoded}")
```

---

## Next Steps

- See `../README.md` for full API documentation
- See `../USAGE_GUIDE.md` for detailed usage guide
- See `../tests/` for more code examples
- Run `pytest ../tests/` to verify installation

---