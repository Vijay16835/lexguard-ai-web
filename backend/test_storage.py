import asyncio
import os
import sys

# add backend path to sys
sys.path.append(os.path.abspath('backend'))

from app.core.config import settings
from supabase import create_client, Client

async def test_storage():
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    try:
        # test listing
        files = supabase.storage.from_("legal-documents").list("users/wfE1RoROvqTch3cKQIRtg2mCSsg1/documents")
        if files:
            print("First file:", files[0])
            size = files[0].get('metadata', {}).get('size', 0)
            print("Size:", size)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_storage())
