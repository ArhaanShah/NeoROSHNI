from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.security import hash_password  # noqa: E402
from app.database import db_session_factory  # noqa: E402
from app.models.auth import User, UserProfile  # noqa: E402
from app.schemas.validators import validate_phone_number  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the first NeoROSHNI commander account.")
    parser.add_argument("--email", required=True, help="Commander email address.")
    parser.add_argument("--password", required=True, help="Commander password.")
    parser.add_argument("--phone-number", required=True, help="Commander phone number in E.164 format.")
    parser.add_argument("--full-name", required=True, help="Commander full name.")
    parser.add_argument(
        "--update-password",
        action="store_true",
        help="Update only the password when a commander with this email already exists.",
    )
    return parser.parse_args()


async def create_first_commander(args: argparse.Namespace) -> int:
    validate_phone_number(args.phone_number)

    async with db_session_factory() as session:
        existing_user = await session.scalar(select(User).where(User.email == args.email))
        if existing_user is not None:
            if not args.update_password:
                print(
                    "Commander email already exists. Re-run with --update-password to rotate the password.",
                    file=sys.stderr,
                )
                return 1
            if existing_user.role != "commander":
                print("Existing user is not a commander; refusing to update it.", file=sys.stderr)
                return 1

            existing_user.hashed_password = hash_password(args.password)
            await session.commit()
            print(f"Updated commander password for {args.email}.")
            return 0

        existing_phone = await session.scalar(select(User).where(User.phone_number == args.phone_number))
        if existing_phone is not None:
            print("Phone number already belongs to another user.", file=sys.stderr)
            return 1

        user = User(
            email=args.email,
            hashed_password=hash_password(args.password),
            phone_number=args.phone_number,
            role="commander",
            is_active=True,
        )
        session.add(user)
        await session.flush()
        session.add(UserProfile(user_id=user.user_id, full_name=args.full_name))

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            print("Commander could not be created because of a database conflict.", file=sys.stderr)
            return 1

        print(f"Created commander account for {args.email}.")
        return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(create_first_commander(args))


if __name__ == "__main__":
    raise SystemExit(main())
