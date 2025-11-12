# LSB Watermarking - Usage Guide

## Quick Start Guide

### 1. Installation

```bash
cd lsb_wm
pip install -r requirements.txt
```

### 2. Run the Demo

#### Option A: With Your Own Image
```bash
cd examples
python demo_basic.py /path/to/your/image.png
```

#### Option B: Auto-Generate Sample Image
```bash
cd examples
python demo_basic.py
```

The demo will:
- Load or create an image
- Perform 0-bit watermarking (detection)
- Perform multi-bit watermarking (30-bit message)
- Save watermarked images to `../output/`
- Display results and statistics

### 3. Expected Output

```
======================================================================
                        LSB Watermarking Demo                         
======================================================================

Using provided image: ../input/sample.png

✓ Image validated: (512, 512), mode: RGB

======================================================================
DEMO 1: 0-bit Watermarking (Detection Only)
======================================================================
Loading image: ../input/sample.png
✓ Loaded image: (512, 512), mode: RGB
✓ Carrier seed: 12345
✓ Embedding 1000 pixels with pattern 'checksum'
✓ Watermark embedded successfully
✓ PSNR: 48.23 dB (higher is better, >40 is excellent)
✓ Saved watermarked image to output/demo_0bit_watermarked.png

--- Detection Phase ---
✓ Watermark detected: True
✓ Confidence: 0.9987
✓ Pattern match: 0.9987

--- Testing with wrong carrier ---
✓ Watermark detected: False
✓ Confidence: 0.5123

--- Testing on original image (no watermark) ---
✓ Watermark detected: False
✓ Confidence: 0.4956

✅ 0-bit watermarking demo completed!

======================================================================
DEMO 2: Multi-bit Watermarking (Message Encoding)
======================================================================
Loading image: ../input/sample.png
✓ Loaded image: (512, 512), mode: RGB
✓ Message length: 30 bits
✓ Message: [1 0 1 1 0 0 1 0 1 1]... (showing first 10 bits)
✓ Carrier seed: 42
✓ Redundancy: 3x (for error correction)
✓ Message embedded successfully
✓ PSNR: 47.89 dB
✓ Saved watermarked image to output/demo_multibit_watermarked.png

--- Extraction Phase ---
✓ Message extracted successfully
✓ Decoded message: [1 0 1 1 0 0 1 0 1 1]... (showing first 10 bits)
✓ Bit accuracy: 100.00%
✓ Bit errors: 0 / 30

✅ Perfect recovery! All bits match.

✅ Multi-bit watermarking demo completed!

======================================================================
              All demos completed successfully!
======================================================================

Output images saved to: ../output/
  - demo_0bit_watermarked.png
  - demo_multibit_watermarked.png
```

## Using the API in Your Code

### Example 1: Simple Detection Watermark

```python
from PIL import Image
import numpy as np
from lsb_wm import embed_0bit, detect_0bit

# Load your image
img = Image.open('my_image.png')

# Embed watermark
carrier = np.array([12345])  # Your secret key
watermarked = embed_0bit(img, carrier, {'num_pixels': 1000})
watermarked.save('watermarked.png')

# Later, detect watermark
result = detect_0bit(watermarked, carrier, {'num_pixels': 1000})
if result['detected']:
    print(f"Watermark found! Confidence: {result['confidence']:.2%}")
```

### Example 2: Encode User Transaction

```python
from PIL import Image
import numpy as np
from lsb_wm import embed_multibit, extract_multibit

# Load image
img = Image.open('nft_image.png')

# Create message (e.g., owner_ID=15, buyer_ID=23)
owner_id = 15    # Binary: 001111
buyer_id = 23    # Binary: 010111
# Combine into 30-bit message (15 bits each with padding)
message = np.array([
    0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,  # owner: 15
    0,0,0,0,0,0,0,0,0,0,1,0,1,1,1   # buyer: 23
], dtype=np.uint8)

# Embed
carrier = np.array([42])
params = {'num_bits': 30, 'redundancy': 3}
watermarked = embed_multibit(img, message, carrier, params)
watermarked.save('watermarked_nft.png')

# Extract
decoded = extract_multibit(watermarked, carrier, params)
print(f"Owner ID: {int(''.join(map(str, decoded[:15])), 2)}")
print(f"Buyer ID: {int(''.join(map(str, decoded[15:])), 2)}")
```

### Example 3: Batch Processing

```python
from PIL import Image
import numpy as np
from lsb_wm import embed_multibit
import os

# Process multiple images
input_dir = 'input_images/'
output_dir = 'watermarked_images/'
os.makedirs(output_dir, exist_ok=True)

carrier = np.array([12345])
message = np.random.randint(0, 2, 30, dtype=np.uint8)
params = {'num_bits': 30, 'redundancy': 3}

for filename in os.listdir(input_dir):
    if filename.endswith(('.png', '.jpg', '.jpeg')):
        img = Image.open(os.path.join(input_dir, filename))
        watermarked = embed_multibit(img, message, carrier, params)
        watermarked.save(os.path.join(output_dir, f'wm_{filename}'))
        print(f"✓ Processed: {filename}")
```

## Running Tests

```bash
# Run all tests
cd lsb_wm
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_encode.py -v
python -m pytest tests/test_decode.py -v

# Run with coverage (if pytest-cov installed)
python -m pytest tests/ --cov=lsb_wm --cov-report=html
```

## Understanding Parameters

### Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `carrier` | np.ndarray | Required | Secret key for pixel selection (seed) |
| `num_pixels` | int | 1000 | Number of pixels to modify (0-bit) |
| `num_bits` | int | Required | Message length (multi-bit) |
| `redundancy` | int | 3 | Times to repeat each bit |
| `channels` | list | [0,1,2] | RGB channels to use |
| `pattern` | str | 'alternating' | Pattern type for 0-bit |
| `threshold` | float | 0.7 | Detection threshold (0-bit) |

### Choosing Parameters

**num_pixels** (0-bit):
- More pixels = stronger watermark, more changes
- Typical: 500-2000 for 512×512 image
- Rule of thumb: 0.5-1% of total pixels

**redundancy** (multi-bit):
- Higher = more robust, needs more capacity
- No attacks: redundancy=1-2
- JPEG/noise: redundancy=3-5
- Heavy attacks: redundancy=7-10

**channels**:
- `[0,1,2]` = RGB (max capacity)
- `[1]` = Green only (less visible)
- `[0,2]` = Red+Blue (compromise)

## Troubleshooting

### Issue: "Image too small" error

**Solution**: Reduce message length or redundancy, or use larger image.

```python
# Calculate required capacity
total_bits = num_bits * redundancy
pixels_needed = total_bits / len(channels)
image_capacity = height * width

if pixels_needed > image_capacity:
    # Reduce redundancy or message length
    redundancy = int((height * width * len(channels)) / num_bits)
```

### Issue: Low detection confidence

**Solution**: 
1. Check you're using the correct carrier
2. Increase num_pixels
3. Verify image hasn't been modified
4. Try different pattern type

### Issue: Bit errors in extracted message

**Solution**:
1. Increase redundancy
2. Avoid saving as JPEG (use PNG)
3. Don't resize or transform watermarked image
4. Use more channels

## Performance Tips

### Speed Optimization
- Use smaller `num_pixels` for 0-bit
- Use lower `redundancy` for multi-bit
- Process images in batch
- Use only necessary channels

### Quality Optimization
- Higher redundancy for noisy environments
- More pixels for stronger 0-bit detection
- Use all RGB channels for capacity
- Monitor PSNR (should be >40 dB)

### Capacity Calculation
```python
# Maximum message capacity
height, width = image.size
max_capacity = (height * width * 3) / redundancy

# Example: 512×512 image, redundancy=3
# max_capacity = (512 * 512 * 3) / 3 = 262,144 bits
```

## Common Use Cases

### 1. NFT Ownership Tracking
- Embed owner_ID + buyer_ID (30 bits)
- Use high redundancy (5-7)
- Store carrier securely
- Update watermark on each sale

### 2. Copyright Protection
- Use 0-bit detection
- High num_pixels (2000+)
- Unique carrier per artist
- Batch process portfolio

### 3. Leak Tracing
- Embed unique ID per recipient
- High redundancy
- Log carrier-user mapping
- Trace leaked copies

### 4. Prototype Testing
- Quick embedding (<0.5s)
- Test different parameters
- Validate workflow
- Benchmark performance

## Additional Resources

- **README.md** - Full documentation
- **PHASE1_SUMMARY.md** - Implementation details
- **API Reference** - See README.md
- **Tests** - See `tests/` for examples

## Support & Contributing

For issues or questions, please refer to the main project documentation or open an issue on the repository.

---

**Happy Watermarking! 🎨🔐**

