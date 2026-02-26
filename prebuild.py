import nltk
import os

# Set custom path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NLTK_DATA_DIR = os.path.join(BASE_DIR, 'Voice2sign', 'nltk_data')

if not os.path.exists(NLTK_DATA_DIR):
    os.makedirs(NLTK_DATA_DIR)

print(f"📦 Downloading NLTK data to {NLTK_DATA_DIR}...")

packages = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger', 'omw-1.4']

for pkg in packages:
    print(f" - Downloading {pkg}...")
    nltk.download(pkg, download_dir=NLTK_DATA_DIR)

print("✅ NLTK data ready!")
