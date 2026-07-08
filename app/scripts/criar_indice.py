import sys
import os

# Ensure the project root is available in sys.path.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.utils.embedding_utils import create_index

def main():
    try:
        print("Creating the document index...")
        create_index()
        print("✅ Index created successfully. You can start SOFIA normally.")
    except Exception as e:
        print(f"❌ Failed to create the index: {e}")

if __name__ == "__main__":
    main()
