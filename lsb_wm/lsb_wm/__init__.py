"""
LSB Watermarking Package

A simplified watermarking system using LSB (Least Significant Bit) technique.
Compatible with wm_codes API but simpler and faster.
"""

__version__ = "0.1.0"
__author__ = "NFT-Based Data Marketplace Team"

from .encode import embed_0bit, embed_multibit
from .decode import detect_0bit, extract_multibit

__all__ = [
    'embed_0bit',
    'embed_multibit', 
    'detect_0bit',
    'extract_multibit',
]

