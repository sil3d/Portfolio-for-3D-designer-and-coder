
import requests
import os

url = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://princegildasmk.up.railway.app/"
# Ensure directory exists
output_dir = r"d:\portfolio\code\Projet Portfolio\Portfolio\Portofolio\portfolio\app\static\images"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

output_path = os.path.join(output_dir, "qr_portfolio.png")

print(f"Downloading QR code to {output_path}...")
try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print("QR Code saved successfully.")
    else:
        print(f"Failed to download QR code. Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
