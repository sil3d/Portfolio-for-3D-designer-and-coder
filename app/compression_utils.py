"""
Compression utilities for file storage in database
Uses zlib for fast, efficient compression with configurable levels
"""

import zlib

# Compression level: 1 (fastest) to 9 (best compression)
# Level 6 is a good balance between speed and compression ratio
COMPRESSION_LEVEL = 6

def compress_file(data: bytes) -> bytes:
    """
    Compress binary data using zlib
    
    Args:
        data: Raw binary data to compress
        
    Returns:
        Compressed binary data
    """
    if not data:
        return data
    
    return zlib.compress(data, level=COMPRESSION_LEVEL)


def decompress_file(data: bytes) -> bytes:
    """
    Decompress binary data that was compressed with zlib
    
    Args:
        data: Compressed binary data
        
    Returns:
        Decompressed binary data
    """
    if not data:
        return data
    
    try:
        return zlib.decompress(data)
    except zlib.error:
        # If decompression fails, assume data is not compressed
        # This allows backward compatibility with existing uncompressed data
        return data


def get_compression_ratio(original_size: int, compressed_size: int) -> float:
    """
    Calculate compression ratio as a percentage
    
    Args:
        original_size: Size of original data in bytes
        compressed_size: Size of compressed data in bytes
        
    Returns:
        Compression ratio as percentage (e.g., 65.5 means 65.5% of original size)
    """
    if original_size == 0:
        return 0.0
    
    return (compressed_size / original_size) * 100


def format_size(size_bytes: int) -> str:
    """
    Format byte size to human-readable string
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB", "500 KB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
