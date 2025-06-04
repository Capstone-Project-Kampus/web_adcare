import sys
import os
from dotenv import load_dotenv

# Tentukan root directory aplikasi
root = "/home/ubuntu/web_adcare"

# Tambahkan root ke sys.path
sys.path.insert(0, root)

# Pindah ke direktori aplikasi sebelum load dotenv
os.chdir(root)

# Load .env file
load_dotenv()

# Import aplikasi Flask
from app import app as application