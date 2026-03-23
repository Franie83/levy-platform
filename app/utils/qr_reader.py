# app/utils/qr_reader.py
import os
import tempfile
import subprocess
import base64
from PIL import Image
import io

def read_qr_code_from_image(image_data):
    """Read QR code from uploaded image data"""
    try:
        # Try using zbar if available (via command line)
        # Save image temporarily
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(image_data)
            tmp_path = tmp.name
        
        # Try to use zbarimg if installed
        try:
            result = subprocess.run(['zbarimg', '-q', tmp_path], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                qr_data = result.stdout.strip()
                if qr_data.startswith('QR-Code:'):
                    qr_data = qr_data[8:]
                os.unlink(tmp_path)
                return qr_data
        except:
            pass
        
        # Alternative: Try to use Python QR code library
        try:
            from pyzbar import pyzbar
            import numpy as np
            
            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img)
            decoded = pyzbar.decode(img_array)
            if decoded:
                os.unlink(tmp_path)
                return decoded[0].data.decode('utf-8')
        except ImportError:
            pass
        
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        
        return None
    except Exception as e:
        print(f"Error reading QR code: {e}")
        return None