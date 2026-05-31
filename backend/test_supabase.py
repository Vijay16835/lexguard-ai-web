import sys
sys.path.insert(0, '.')
from app.core.config import settings
from supabase import create_client, Client
import traceback

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
# List files in the bucket
try:
    res = supabase.storage.from_("legal-documents").list("users")
    print("Users directory:", res)
    # Let's list a specific user's directory
    users = [f['name'] for f in res if f['name'] != '.emptyFolderPlaceholder']
    if users:
        user_id = users[0]
        res2 = supabase.storage.from_("legal-documents").list(f"users/{user_id}/documents")
        print(f"Documents for {user_id}:", res2)
        if res2 and res2[0]['name'] != '.emptyFolderPlaceholder':
            doc_name = res2[0]['name']
            path = f"users/{user_id}/documents/{doc_name}"
            print("Trying to download:", path)
            download_res = supabase.storage.from_("legal-documents").download(path)
            print("Downloaded bytes:", len(download_res))
except Exception as e:
    traceback.print_exc()
