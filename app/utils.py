import io
import gzip
import requests
import base64
import logging

def compress_file(data):
    """Compresses file data using GZIP."""
    if not data:
        return None
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode='wb') as f:
        f.write(data)
    return out.getvalue()

def decompress_file(data):
    """Decompresses GZIP compressed file data."""
    if not data:
        return b""
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data), mode='rb') as f:
            return f.read()
    except Exception as e:
        print(f"Error decompressing file: {e}")
        return data  # Return original if not compressed

def get_location_from_ip(ip_address):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'fail':
            return 'Unknown Location'
        
        city = data.get('city', 'Unknown')
        region = data.get('regionName', 'Unknown')
        country = data.get('country', 'Unknown')
        location = f"{city}, {region}, {country}"
        
        return location
    
    except requests.RequestException as e:
        print(f"Error retrieving location: {e}")
        return 'Unknown Location'

def allowed_file(filename, allowed_extensions):
    """Vérifie si le fichier a une extension autorisée."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def to_base32(string):
    return base64.b32encode(string.encode()).decode().rstrip('=')
