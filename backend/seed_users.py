"""
Seed initial users into the database.
Run this script once to create default admin and test users.
"""
from app.core.database import SessionLocal, init_db
from app.models.user import UserDB, UserRole
from app.core.security import hash_password

def seed_users():
    """Create initial users if they don't exist"""
    init_db()  # Ensure tables are created
    
    db = SessionLocal()
    try:
        # Check if users already exist
        existing_users = db.query(UserDB).count()
        if existing_users > 0:
            print(f"Database already has {existing_users} user(s). Skipping seed.")
            return
        
        # Create default users
        users = [
            {
                "email": "admin@example.com",
                "password": "admin123",
                "role": UserRole.admin
            },
            {
                "email": "engineer@example.com",
                "password": "engineer123",
                "role": UserRole.engineer
            },
            {
                "email": "hr@example.com",
                "password": "hr123",
                "role": UserRole.hr
            }
        ]
        
        for user_data in users:
            user = UserDB(
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                role=user_data["role"],
                is_active=1
            )
            db.add(user)
        
        db.commit()
        print(f"✓ Successfully created {len(users)} users!")
        print("\nDefault credentials:")
        for user_data in users:
            print(f"  - {user_data['email']} / {user_data['password']}")
        
    except Exception as e:
        print(f"Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
