"""
Unit tests for decode module
"""

import pytest
import numpy as np
from PIL import Image
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lsb_wm.encode import embed_0bit, embed_multibit
from lsb_wm.decode import (
    extract_bits,
    majority_vote,
    compute_bit_accuracy,
    detect_0bit,
    extract_multibit
)


class TestExtractBits:
    """Test bit extraction function"""
    
    def test_basic_extraction(self):
        """Test basic bit extraction"""
        # Create image with known LSBs
        img_array = np.zeros((10, 10, 3), dtype=np.uint8)
        img_array[0, 0, 0] = 0b00000001  # LSB = 1
        img_array[0, 1, 0] = 0b00000000  # LSB = 0
        img_array[1, 0, 0] = 0b00000001  # LSB = 1
        
        positions = np.array([[0, 0], [0, 1], [1, 0]])
        channels = [0]
        num_bits = 3
        
        extracted = extract_bits(img_array, positions, channels, num_bits)
        
        expected = np.array([1, 0, 1], dtype=np.uint8)
        np.testing.assert_array_equal(extracted, expected)
    
    def test_multi_channel_extraction(self):
        """Test extraction from multiple channels"""
        img_array = np.zeros((10, 10, 3), dtype=np.uint8)
        
        # Set LSBs
        img_array[0, 0, 0] = 1  # R: 1
        img_array[0, 0, 1] = 0  # G: 0
        img_array[0, 0, 2] = 1  # B: 1
        img_array[0, 1, 0] = 1  # R: 1
        img_array[0, 1, 1] = 0  # G: 0
        img_array[0, 1, 2] = 0  # B: 0
        
        positions = np.array([[0, 0], [0, 1]])
        channels = [0, 1, 2]
        num_bits = 6
        
        extracted = extract_bits(img_array, positions, channels, num_bits)
        
        expected = np.array([1, 0, 1, 1, 0, 0], dtype=np.uint8)
        np.testing.assert_array_equal(extracted, expected)
    
    def test_extraction_stops_at_num_bits(self):
        """Test that extraction stops at num_bits"""
        img_array = np.ones((10, 10, 3), dtype=np.uint8)
        positions = np.array([[i, i] for i in range(10)])
        channels = [0, 1, 2]
        num_bits = 5  # Less than available
        
        extracted = extract_bits(img_array, positions, channels, num_bits)
        
        assert len(extracted) == 5


class TestMajorityVote:
    """Test majority voting function"""
    
    def test_perfect_redundancy(self):
        """Test with perfect redundancy (no errors)"""
        # Message: [1, 0, 1]
        # With redundancy 3: [1,1,1, 0,0,0, 1,1,1]
        redundant = np.array([1, 1, 1, 0, 0, 0, 1, 1, 1], dtype=np.uint8)
        redundancy = 3
        
        decoded = majority_vote(redundant, redundancy)
        
        expected = np.array([1, 0, 1], dtype=np.uint8)
        np.testing.assert_array_equal(decoded, expected)
    
    def test_error_correction(self):
        """Test error correction with majority vote"""
        # Message: [1, 0]
        # With redundancy 3 and 1 error each: [1,1,0, 0,0,1]
        redundant = np.array([1, 1, 0, 0, 0, 1], dtype=np.uint8)
        redundancy = 3
        
        decoded = majority_vote(redundant, redundancy)
        
        expected = np.array([1, 0], dtype=np.uint8)
        np.testing.assert_array_equal(decoded, expected)
    
    def test_high_redundancy(self):
        """Test with high redundancy"""
        # Message: [1]
        # With redundancy 5 and 2 errors: [1,1,1,0,0]
        redundant = np.array([1, 1, 1, 0, 0], dtype=np.uint8)
        redundancy = 5
        
        decoded = majority_vote(redundant, redundancy)
        
        expected = np.array([1], dtype=np.uint8)
        np.testing.assert_array_equal(decoded, expected)


class TestComputeBitAccuracy:
    """Test bit accuracy computation"""
    
    def test_perfect_accuracy(self):
        """Test with perfectly matching bits"""
        decoded = np.array([1, 0, 1, 1, 0], dtype=np.uint8)
        original = np.array([1, 0, 1, 1, 0], dtype=np.uint8)
        
        accuracy = compute_bit_accuracy(decoded, original)
        
        assert accuracy == 1.0
    
    def test_zero_accuracy(self):
        """Test with all bits wrong"""
        decoded = np.array([1, 1, 1, 1, 1], dtype=np.uint8)
        original = np.array([0, 0, 0, 0, 0], dtype=np.uint8)
        
        accuracy = compute_bit_accuracy(decoded, original)
        
        assert accuracy == 0.0
    
    def test_partial_accuracy(self):
        """Test with some bits correct"""
        decoded = np.array([1, 0, 1, 0], dtype=np.uint8)
        original = np.array([1, 1, 0, 0], dtype=np.uint8)
        
        accuracy = compute_bit_accuracy(decoded, original)
        
        assert accuracy == 0.5  # 2 out of 4 correct
    
    def test_different_lengths(self):
        """Test with different length arrays"""
        decoded = np.array([1, 0, 1, 0, 1], dtype=np.uint8)
        original = np.array([1, 0, 1], dtype=np.uint8)
        
        # Should compare only the minimum length
        accuracy = compute_bit_accuracy(decoded, original)
        
        assert accuracy == 1.0  # First 3 bits match


class TestDetect0bit:
    """Test 0-bit watermark detection"""
    
    def test_detect_watermarked_image(self):
        """Test detection of watermarked image"""
        # Create and watermark image
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        carrier = np.array([1, 2, 3])
        params_embed = {'num_pixels': 100, 'pattern': 'alternating'}
        
        watermarked = embed_0bit(img, carrier, params_embed)
        
        # Detect watermark
        params_detect = {'num_pixels': 100, 'pattern': 'alternating', 'threshold': 0.7}
        result = detect_0bit(watermarked, carrier, params_detect)
        
        assert result['detected'] == True
        assert result['confidence'] > 0.9
        assert result['pattern_match'] > 0.9
    
    def test_no_watermark_detection(self):
        """Test with non-watermarked image"""
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        carrier = np.array([1, 2, 3])
        
        params_detect = {'num_pixels': 100, 'pattern': 'alternating', 'threshold': 0.7}
        result = detect_0bit(img, carrier, params_detect)
        
        # Should have low confidence (random match ~0.5)
        assert result['confidence'] < 0.7
    
    def test_wrong_carrier(self):
        """Test with wrong carrier"""
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        carrier1 = np.array([1, 2, 3])
        carrier2 = np.array([4, 5, 6])  # Different carrier
        
        params = {'num_pixels': 100, 'pattern': 'alternating'}
        watermarked = embed_0bit(img, carrier1, params)
        
        # Try to detect with wrong carrier
        result = detect_0bit(watermarked, carrier2, params)
        
        # Should not detect (or low confidence)
        assert result['confidence'] < 0.7
    
    def test_different_patterns(self):
        """Test detection with different pattern types"""
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        carrier = np.array([1, 2, 3])
        
        patterns = ['alternating', 'ones', 'checksum']
        
        for pattern in patterns:
            params = {'num_pixels': 100, 'pattern': pattern}
            watermarked = embed_0bit(img, carrier, params)
            result = detect_0bit(watermarked, carrier, params)
            
            assert result['detected'] == True
            assert result['confidence'] > 0.9


class TestExtractMultibit:
    """Test multi-bit message extraction"""
    
    def test_basic_extraction(self):
        """Test basic message extraction"""
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        message = np.array([1, 0, 1, 1, 0, 0, 1, 0], dtype=np.uint8)
        carrier = np.array([42])
        
        params_embed = {'redundancy': 3, 'num_bits': 8}
        watermarked = embed_multibit(img, message, carrier, params_embed)
        
        params_extract = {'num_bits': 8, 'redundancy': 3}
        decoded = extract_multibit(watermarked, carrier, params_extract)
        
        np.testing.assert_array_equal(decoded, message)
    
    def test_perfect_recovery(self):
        """Test perfect message recovery"""
        img = Image.new('RGB', (200, 200), color=(128, 128, 128))
        message = np.random.randint(0, 2, size=30, dtype=np.uint8)
        carrier = np.array([123])
        
        params_embed = {'redundancy': 5, 'num_bits': 30}
        watermarked = embed_multibit(img, message, carrier, params_embed)
        
        params_extract = {'num_bits': 30, 'redundancy': 5}
        decoded = extract_multibit(watermarked, carrier, params_extract)
        
        accuracy = compute_bit_accuracy(decoded, message)
        assert accuracy == 1.0
    
    def test_different_redundancy_values(self):
        """Test with different redundancy values"""
        img = Image.new('RGB', (150, 150), color=(128, 128, 128))
        message = np.array([1, 0, 1, 0, 1], dtype=np.uint8)
        carrier = np.array([42])
        
        for redundancy in [1, 3, 5, 7]:
            params_embed = {'redundancy': redundancy, 'num_bits': 5}
            watermarked = embed_multibit(img, message, carrier, params_embed)
            
            params_extract = {'num_bits': 5, 'redundancy': redundancy}
            decoded = extract_multibit(watermarked, carrier, params_extract)
            
            np.testing.assert_array_equal(decoded, message)
    
    def test_long_message(self):
        """Test with longer messages"""
        img = Image.new('RGB', (300, 300), color=(128, 128, 128))
        message = np.random.randint(0, 2, size=100, dtype=np.uint8)
        carrier = np.array([999])
        
        params_embed = {'redundancy': 2, 'num_bits': 100}
        watermarked = embed_multibit(img, message, carrier, params_embed)
        
        params_extract = {'num_bits': 100, 'redundancy': 2}
        decoded = extract_multibit(watermarked, carrier, params_extract)
        
        accuracy = compute_bit_accuracy(decoded, message)
        assert accuracy >= 0.95  # Should be very high
    
    def test_missing_num_bits_error(self):
        """Test error when num_bits not provided"""
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        carrier = np.array([42])
        
        params = {'redundancy': 3}  # Missing num_bits
        
        with pytest.raises(ValueError):
            extract_multibit(img, carrier, params)


class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_0bit_embed_and_detect(self):
        """Test complete 0-bit workflow"""
        img = Image.new('RGB', (150, 150), color=(100, 150, 200))
        carrier = np.array([12345])
        
        # Embed
        params_embed = {'num_pixels': 500, 'pattern': 'checksum'}
        watermarked = embed_0bit(img, carrier, params_embed)
        
        # Detect
        params_detect = {'num_pixels': 500, 'pattern': 'checksum', 'threshold': 0.8}
        result = detect_0bit(watermarked, carrier, params_detect)
        
        assert result['detected'] == True
        assert result['confidence'] > 0.95
    
    def test_multibit_embed_and_extract(self):
        """Test complete multi-bit workflow"""
        img = Image.new('RGB', (200, 200), color=(100, 150, 200))
        message = np.array([1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1], dtype=np.uint8)
        carrier = np.array([98765])
        
        # Embed
        params_embed = {'redundancy': 4, 'num_bits': 15}
        watermarked = embed_multibit(img, message, carrier, params_embed)
        
        # Extract
        params_extract = {'num_bits': 15, 'redundancy': 4}
        decoded = extract_multibit(watermarked, carrier, params_extract)
        
        # Verify
        np.testing.assert_array_equal(decoded, message)
        accuracy = compute_bit_accuracy(decoded, message)
        assert accuracy == 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

