import os
import psycopg2
from dotenv import load_dotenv
import uuid

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def test_supabase_integration():
    print("Testing Supabase PostgreSQL Connection...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        print("✅ 1. Database connection successful.")
        
        # Test Tables
        tables_to_check = ['users', 'documents', 'analysis']
        for table in tables_to_check:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                print(f"✅ 2/3/4. '{table}' table verified (Record count: {count}).")
            except Exception as e:
                print(f"❌ Failed to query '{table}' table: {e}")
                conn.rollback()

        # Test CRUD Operations
        print("\nTesting CRUD Operations on 'users' table...")
        
        # 1. Create
        test_email = f"test_crud_{uuid.uuid4().hex[:8]}@example.com"
        try:
            cur.execute("""
                INSERT INTO users (full_name, email, hashed_password)
                VALUES (%s, %s, %s) RETURNING id;
            """, ("Test User", test_email, "dummy_hash"))
            user_id = cur.fetchone()[0]
            print(f"✅ CREATE: Inserted test user (ID: {user_id})")
            
            # 2. Read
            cur.execute("SELECT email FROM users WHERE id = %s;", (user_id,))
            read_email = cur.fetchone()[0]
            if read_email == test_email:
                print(f"✅ READ: Successfully read test user (Email: {read_email})")
            else:
                print("❌ READ: Email mismatch")
                
            # 3. Update
            new_name = "Updated Test User"
            cur.execute("UPDATE users SET full_name = %s WHERE id = %s;", (new_name, user_id))
            cur.execute("SELECT full_name FROM users WHERE id = %s;", (user_id,))
            updated_name = cur.fetchone()[0]
            if updated_name == new_name:
                print(f"✅ UPDATE: Successfully updated test user (Name: {updated_name})")
            else:
                print("❌ UPDATE: Name mismatch")
                
            # 4. Delete
            cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
            cur.execute("SELECT COUNT(*) FROM users WHERE id = %s;", (user_id,))
            del_count = cur.fetchone()[0]
            if del_count == 0:
                print("✅ DELETE: Successfully deleted test user")
            else:
                print("❌ DELETE: User not deleted")
                
        except Exception as e:
            print(f"❌ CRUD operation failed: {e}")
            conn.rollback()
            
        conn.commit()
        cur.close()
        conn.close()
        print("\n✅ Supabase integration verification complete.")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    test_supabase_integration()
