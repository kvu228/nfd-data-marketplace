# LSB Watermarking Module

Module watermarking sử dụng thuật toán LSB (Least Significant Bit) với interface tương tự SSL watermarking.

## Tổng Quan

Module này cung cấp chức năng watermarking sử dụng phương pháp LSB - một kỹ thuật steganography đơn giản và hiệu quả. Module được thiết kế với interface tương tự `ssl_watermarking` để có thể thay thế dễ dàng trong hệ thống.

## Cấu Trúc

```
lsb_watermarking/
├── __init__.py          # Package initialization
├── main_multibit.py     # Main Watermark class
├── encode.py            # LSB encoding functions
├── decode.py            # LSB decoding functions
├── utils.py             # Utility functions
├── input/               # Input directory for images
│   └── 0/              # Subdirectory for single image processing
└── output/             # Output directory
    └── imgs/           # Watermarked images
```

## Sử Dụng

### Basic Usage

```python
from lsb_watermarking.main_multibit import Watermark

# Khởi tạo
wm = Watermark()

# Set watermark message (owner_id + buyer_id)
wm.set_watermark(owner_id=10, buyer_id=20)

# Watermark một image
wm.watermark_image("path/to/image.png")

# Extract watermark
owner_id, buyer_id = wm.extract_watermark("path/to/watermarked_image.png")
```

### Interface Tương Tự SSL Watermarking

Module này có interface hoàn toàn tương tự `ssl_watermarking.main_multibit.Watermark`:

- `__init__()`: Khởi tạo với các tham số mặc định
- `set_watermark(owner_id, buyer_id)`: Set watermark message
- `watermark_image(img_filepath)`: Watermark một image
- `extract_watermark(img_filepath)`: Extract watermark từ image
- `watermark()`: Watermark batch images
- `decode_watermark()`: Decode batch images

## Thuật Toán LSB

LSB (Least Significant Bit) watermarking hoạt động bằng cách:

1. **Encoding:**
   - Thay thế bit ít quan trọng nhất (LSB) của mỗi pixel với bit của watermark
   - Watermark được nhúng tuần tự vào các pixel từ trái sang phải, từ trên xuống dưới

2. **Decoding:**
   - Đọc LSB của các pixel để extract watermark
   - Reconstruct watermark message từ các bits đã đọc

### Ưu Điểm

- Đơn giản và nhanh
- Không cần model deep learning
- Watermark gần như không nhìn thấy bằng mắt thường
- Dễ implement và maintain

### Nhược Điểm

- Dễ bị phát hiện bằng steganalysis
- Dễ bị mất khi image bị nén hoặc chỉnh sửa
- Không robust như SSL watermarking

## So Sánh với SSL Watermarking

| Tính năng | LSB Watermarking | SSL Watermarking |
|-----------|------------------|------------------|
| Độ phức tạp | Thấp | Cao |
| Tốc độ | Nhanh | Chậm (cần GPU) |
| Robustness | Thấp | Cao |
| Cần model DL | Không | Có |
| Dung lượng | Cao | Trung bình |

## Yêu Cầu

- Python 3.x
- numpy
- Pillow (PIL)

## Lưu Ý

1. LSB watermarking phù hợp cho môi trường development và testing
2. Đối với production, nên cân nhắc sử dụng SSL watermarking hoặc các phương pháp robust hơn
3. Watermark có thể bị mất khi image bị:
   - Nén lossy (JPEG)
   - Resize
   - Chỉnh sửa màu sắc
   - Crop

## Tích Hợp Vào Hệ Thống

Để sử dụng LSB watermarking thay cho SSL watermarking, chỉ cần thay đổi import:

```python
# Thay vì:
from ssl_watermarking.main_multibit import Watermark

# Sử dụng:
from lsb_watermarking.main_multibit import Watermark
```

Tất cả các methods và interface đều tương tự, không cần thay đổi code khác.

