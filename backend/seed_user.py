from app.db.session import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import get_password_hash

def seed_user():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    email = "tvijay1098@gmail.com"
    password = "1098Vijay"
    
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"User {email} already exists. Updating password...")
        user.hashed_password = get_password_hash(password)
        user.is_verified = True
    else:
        print(f"Creating user {email}...")
        new_user = User(
            full_name="Vijay T",
            email=email,
            hashed_password=get_password_hash(password),
            is_verified=True,
            auth_provider="email"
        )
        db.add(new_user)
    
    db.commit()
    db.close()
    print("Done!")

if __name__ == "__main__":
    seed_user()
