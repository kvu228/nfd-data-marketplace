"""
Unit tests for encode module
"""

import pytest
import numpy as np
from PIL import Image
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lsb_wm.encode import (
    select_pixels, 
    embed_bits, 
    compute_psnr, 
    embed_0bit, 
    embed_multibit
)


class TestSelectPixels:
    """Test pixel selection function"""
    
    def test_basic_selection(self):
        """Test basic pixel selection"""
        image_shape = (100, 100)
        carrier = np.array([1, 2, 3])
        num_pixels = 50
        
        positions = select_pixels(image_shape, carrier, num_pixels)
        
        assert positions.shape == (50, 2)
        assert np.all(positions[:, 0] < 100)  # rows < height
        assert np.all(positions[:, 1] < 100)  # cols < width
        assert np.all(positions >= 0)
    
    def test_deterministic(self):
        """Test that selection is deterministic"""
        image_shape = (100, 100)
        carrier = np.array([1, 2, 3])
        num_pixels = 50
        
        positions1 = select_pixels(image_shape, carrier, num_pixels)
        positions2 = select_pixels(image_shape, carrier, num_pixels)
        
        np.testing.assert_array_equal(positions1, positions2)
    
    def test_different_carriers(self):
        """Test that different carriers produce different selections"""
        image_shape = (100, 100)
        carrier1 = np.array([1, 2, 3])
        carrier2 = np.array([4, 5, 6])
        num_pixels = 50
        
        positions1 = select_pixels(image_shape, carrier1, num_pixels)
        positions2 = select_pixels(image_shape, carrier2, num_pixels)
        
        # Should be different
        assert not np.array_equal(positions1, positions2)
    
    def test_max_pixels(self):
        """Test selection with more pixels than available"""
        image_shape = (10, 10)  # Total 100 pixels
        carrier = np.array([1, 2, 3])
        num_pixels = 150  # More than available
        
        positions = select_pixels(image_shape, carrier, num_pixels)
        
        # Should be capped at total pixels
        assert len(positions) <= 100
    
    def test_integer_carrier(self):
        """Test with integer carrier (seed)"""
        image_shape = (100, 100)
        carrier = 42  # Integer seed
        num_pixels = 50
        
        positions = select_pixels(image_shape, carrier, num_pixels)
        
        assert positions.shape == (50, 2)


class TestEmbedBits:
    """Test bit embedding function"""
    
    def test_basic_embedding(self):
        """Test basic bit embedding"""
        img_array = np.random.randint(0, 256, size=(10, 10, 3), dtype=np.uint8)
        positions = np.array([[0, 0], [0, 1], [1, 0]])
        bits = np.array([1, 0, 1], dtype=np.uint8)
        channels = [0]
        
        result = embed_bits(img_array, positions, bits, channels)
        
        # Check that bits were embedded
        assert (result[0, 0, 0] & 1) == 1
        assert (result[0, 1, 0] & 1) == 0
        assert (result[1, 0, 0] & 1) == 1
    
    def test_multi_channel_embedding(self):
        """Test embedding across multiple channels"""
        img_array = np.random.randint(0, 256, size=(10, 10, 3), dtype=np.uint8)
        positions = np.array([[0, 0], [0, 1]])
        bits = np.array([1, 0, 1, 1, 0, 0], dtype=np.uint8)
        channels = [0, 1, 2]  # All channels
        
        result = embed_bits(img_array, positions, bits, channels)
        
        # Check first pixel (all 3 channels)
        assert (result[0, 0, 0] & 1) == 1
        assert (result[0, 0, 1] & 1) == 0
        assert (result[0, 0, 2] & 1) == 1
        
        # Check second pixel (all 3 channels)
        assert (result[0, 1, 0] & 1) == 1
        assert (result[0, 1, 1] & 1) == 0
        assert (result[0, 1, 2] & 1) == 0
    
    def test_insufficient_capacity(self):
        """Test error when not enough capacity"""
        img_array = np.random.randint(0, 256, size=(10, 10, 3), dtype=np.uint8)
        positions = np.array([[0, 0], [0, 1]])  # 2 positions
        bits = np.array([1, 0, 1, 1, 0, 0, 1], dtype=np.uint8)  # 7 bits
        channels = [0, 1, 2]  # 3 channels -> capacity = 2*3 = 6
        
        with pytest.raises(ValueError):
            embed_bits(img_array, positions, bits, channels)
    
    def test_original_not_modified(self):
        """Test that original array is not modified"""
        img_array = np.random.randint(0, 256, size=(10, 10, 3), dtype=np.uint8)
        img_array_copy = img_array.copy()
        positions = np.array([[0, 0], [0, 1]])
        bits = np.array([1, 0], dtype=np.uint8)
        channels = [0]
        
        result = embed_bits(img_array, positions, bits, channels)
        
        # Original should not be modified
        np.testing.assert_array_equal(img_array, img_array_copy)


class TestComputePSNR:
    """Test PSNR computation"""
    
    def test_identical_images(self):
        """Test PSNR of identical images"""
        img = np.random.randint(0, 256, size=(100, 100, 3), dtype=np.uint8)
        
        psnr = compute_psnr(img, img)
        
        assert np.isinf(psnr)
    
    def test_different_images(self):
        """Test PSNR of different images"""
        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.ones((100, 100, 3), dtype=np.uint8)
        
        psnr = compute_psnr(img1, img2)
        
        assert np.isfinite(psnr)
        assert psnr > 0
    
    def test_small_difference(self):
        """Test PSNR with small differences (LSB changes)"""
        img1 = np.random.randint(0, 256, size=(100, 100, 3), dtype=np.uint8)
        img2 = img1.copy()
        
        # Modify only LSBs (should give high PSNR)
        img2[0, 0, 0] = img1[0, 0, 0] ^ 1  # Flip LSB
        
        psnr = compute_psnr(img1, img2)
        
        # PSNR should be very high for LSB changes
        assert psnr > 40


class TestEmbed0bit:
    """Test 0-bit watermark embedding"""
    
    def test_basic_0bit_embedding(self):
        """Test basic 0-bit watermark embedding"""
        # Create test image
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        carrier = np.array([1, 2, 3])
        params = {'num_pixels': 100, 'pattern': 'alternating'}
        
        watermarked = embed_0bit(img, carrier, params)
        
        assert isinstance(watermarked, Image.Image)
        assert watermarked.size == img.size
        assert watermarked.mode == 'RGB'
    
    def test_different_patterns(self):
        """Test different pattern types"""
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        carrier = np.array([1, 2, 3])
        
        patterns = ['alternating', 'ones', 'checksum']
        
        for pattern in patterns:
            params = {'num_pixels': 100, 'pattern': pattern}
            watermarked = embed_0bit(img, carrier, params)
            
            assert isinstance(watermarked, Image.Image)
    
    def test_grayscale_image(self):
        """Test with grayscale image (should convert to RGB)"""
        img = Image.new('L', (100, 100), color=128)
        carrier = np.array([1, 2, 3])
        params = {'num_pixels': 100}
        
        watermarked = embed_0bit(img, carrier, params)
        
        assert isinstance(watermarked, Image.Image)
        assert watermarked.mode == 'RGB'
    
    def test_high_psnr(self):
        """Test that PSNR is high (minimal changes)"""
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        carrier = np.array([1, 2, 3])
        params = {'num_pixels': 100}
        
        watermarked = embed_0bit(img, carrier, params)
        
        # Compute PSNR
        img_array = np.array(img)
        wm_array = np.array(watermarked)
        psnr = compute_psnr(img_array, wm_array)
        
        # PSNR should be very high (only LSB changes)
        assert psnr > 40


class TestEmbedMultibit:
    """Test multi-bit watermark embedding"""
    
    def test_basic_multibit_embedding(self):
        """Test basic multi-bit embedding"""
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        message = np.array([1, 0, 1, 1, 0, 0, 1, 0], dtype=np.uint8)
        carrier = np.array([42])  # Single carrier seed
        params = {'redundancy': 3, 'num_bits': 8}
        
        watermarked = embed_multibit(img, message, carrier, params)
        
        assert isinstance(watermarked, Image.Image)
        assert watermarked.size == img.size
    
    def test_long_message(self):
        """Test with longer message"""
        img = Image.new('RGB', (200, 200), color=(128, 128, 128))
        message = np.random.randint(0, 2, size=100, dtype=np.uint8)
        carrier = np.array([42])
        params = {'redundancy': 2, 'num_bits': 100}
        
        watermarked = embed_multibit(img, message, carrier, params)
        
        assert isinstance(watermarked, Image.Image)
    
    def test_insufficient_capacity_error(self):
        """Test error when image is too small"""
        img = Image.new('RGB', (10, 10), color=(128, 128, 128))
        # Too many bits for small image
        message = np.random.randint(0, 2, size=1000, dtype=np.uint8)
        carrier = np.array([42])
        params = {'redundancy': 3, 'num_bits': 1000}
        
        with pytest.raises(ValueError):
            embed_multibit(img, message, carrier, params)
    
    def test_different_redundancy(self):
        """Test with different redundancy values"""
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        message = np.array([1, 0, 1, 0], dtype=np.uint8)
        carrier = np.array([42])
        
        for redundancy in [1, 3, 5]:
            params = {'redundancy': redundancy, 'num_bits': 4}
            watermarked = embed_multibit(img, message, carrier, params)
            
            assert isinstance(watermarked, Image.Image)
    
    def test_high_psnr_multibit(self):
        """Test that PSNR remains high"""
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        message = np.random.randint(0, 2, size=30, dtype=np.uint8)
        carrier = np.array([42])
        params = {'redundancy': 3, 'num_bits': 30}
        
        watermarked = embed_multibit(img, message, carrier, params)
        
        img_array = np.array(img)
        wm_array = np.array(watermarked)
        psnr = compute_psnr(img_array, wm_array)
        
        # Should still have high PSNR
        assert psnr > 35


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

