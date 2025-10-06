# utils/hash_functions.py
import hashlib

# default shake output length in bytes (32 bytes -> 64 hex chars)
SHAKE_DEFAULT_BYTES = 32

def generate_hash(data, algorithm='sha256', shake_bytes=SHAKE_DEFAULT_BYTES):
    """
    data: bytes or str
    algorithm: name like 'sha256', 'md5', 'blake2b', 'shake_128', etc.
    returns hex string or error string
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    try:
        if algorithm.startswith('shake_'):
            hasher = getattr(hashlib, algorithm)()
            hasher.update(data)
            return hasher.hexdigest(shake_bytes)
        else:
            hasher = getattr(hashlib, algorithm)()
            hasher.update(data)
            return hasher.hexdigest()
    except (AttributeError, TypeError, ValueError):
        return f"[Error] Algorithm '{algorithm}' not supported on this system."

def compare_hashes(hash_a, hash_b):
    return str(hash_a).strip().lower() == str(hash_b).strip().lower()

def verify_file_integrity(file_bytes, expected_hash, algorithm='sha256'):
    actual = generate_hash(file_bytes, algorithm)
    return compare_hashes(actual, expected_hash), actual

def batch_hash_files(file_streams, algorithm='sha256'):
    """
    file_streams: list of (filename, bytes)
    returns list of tuples (filename, hexdigest)
    """
    results = []
    for name, b in file_streams:
        h = generate_hash(b, algorithm)
        results.append((name, h))
    return results
