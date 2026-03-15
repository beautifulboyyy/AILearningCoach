"""
Minimal async SQLAlchemy playground for learning database flow in this project.

Run from project root with:
python tutorials/database/sqlalchemy_playground.py
"""

import asyncio

from sqlalchemy import select

from app.db.session import async_session_maker
from app.models.user import User


async def main() -> None:
    print("=== SQLAlchemy Playground ===")

    async with async_session_maker() as session:
        result = await session.execute(select(User).limit(3))
        users = result.scalars().all()
        print(f"Current user count sample: {len(users)}")
        for user in users:
            print(f"- id={user.id}, username={user.username}, email={user.email}")

    demo_username = "db_demo_user"
    demo_email = "db_demo_user@example.com"

    async with async_session_maker() as session:
        existing_result = await session.execute(
            select(User).filter(User.username == demo_username)
        )
        existing_user = existing_result.scalar_one_or_none()

        if existing_user is None:
            demo_user = User(
                username=demo_username,
                email=demo_email,
                password_hash="demo_hash_only_for_learning",
                is_active=True,
                is_superuser=False,
            )
            session.add(demo_user)
            await session.commit()
            await session.refresh(demo_user)
            print(f"Inserted demo user with id={demo_user.id}")
        else:
            print(f"Demo user already exists with id={existing_user.id}")

    async with async_session_maker() as session:
        verify_result = await session.execute(
            select(User).filter(User.username == demo_username)
        )
        verify_user = verify_result.scalar_one_or_none()
        if verify_user:
            print(
                f"Verified user from database: id={verify_user.id}, "
                f"username={verify_user.username}"
            )


if __name__ == "__main__":
    asyncio.run(main())
