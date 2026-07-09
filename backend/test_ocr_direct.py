import os
import sys
import asyncio
import traceback

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.document_service import extract_text, get_file_extension
from app.services.groq_service import groq_service

async def test_file(file_path, expected_type):
    print("=" * 60)
    print(f"Testing file: {os.path.basename(file_path)} ({expected_type})")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist!")
        return False
        
    file_ext = get_file_extension(file_path)
    print(f"File extension determined: {file_ext}")
    
    # 1. Text extraction
    try:
        print("[EXTRACT] Extracting text...")
        text = extract_text(file_path, file_ext)
        print(f"[EXTRACT] Success! Length = {len(text)}")
        print(f"[EXTRACT] First 500 chars:\n{text[:500]}")
    except Exception as e:
        print(f"[EXTRACT] Failed with exception: {e}")
        traceback.print_exc()
        return False
        
    # 2. AI Analysis
    try:
        print("[AI] Analyzing text with Groq...")
        # Since it calls Groq, let's see if we can run it
        analysis_result = await groq_service.analyze_document(text)
        print(f"[AI] Success! Risk level: {analysis_result.get('risk_level')}")
        print(f"[AI] Summary: {analysis_result.get('summary')}")
        return True
    except Exception as e:
        print(f"[AI] Failed with exception: {e}")
        traceback.print_exc()
        return False

async def main():
    # Let's see if the test files exist in backend/test_files
    test_dir = os.path.join(os.path.dirname(__file__), "test_files")
    
    files = {
        "txt": os.path.join(test_dir, "small.txt"),
        "docx": os.path.join(test_dir, "simple.docx"),
        "pdf_text": os.path.join(test_dir, "text.pdf"),
        "pdf_scanned": os.path.join(test_dir, "scanned.pdf"),
        "jpg": os.path.join(test_dir, "sample.jpg"),
        "jpeg": os.path.join(test_dir, "sample.jpeg"),
        "png": os.path.join(test_dir, "sample.png"),
    }
    
    for key, path in files.items():
        await test_file(path, key)

if __name__ == "__main__":
    asyncio.run(main())
