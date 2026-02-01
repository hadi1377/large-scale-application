import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal, engine, Base
from models import User
from auth import hash_password


async def seed_admin():
    """Seed admin user to the database."""
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if admin already exists
            result = await session.execute(
                select(User).where(User.email == "hadi@gmail.com")
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print("Admin user already exists with email: hadi@gmail.com")
                return
            
            # Create admin user
            admin_user = User(
                email="hadi@gmail.com",
                password=hash_password("secret"),
                main_role="admin",
                full_name="Admin User"
            )
            
            session.add(admin_user)
            await session.commit()
            print("Admin user seeded successfully!")
            print(f"Email: hadi@gmail.com")
            print(f"Password: secret")
            print(f"Role: admin")
            
        except Exception as e:
            await session.rollback()
            print(f"Error seeding admin: {e}")
            raise
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(seed_admin())

