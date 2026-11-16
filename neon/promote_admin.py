"""Promote a registered user. Usage: python neon/promote_admin.py email@example.com"""
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv


async def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python neon/promote_admin.py email@example.com")
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        result = await conn.execute("update users set role='admin' where email=$1", sys.argv[1].lower())
        if result != "UPDATE 1":
            raise SystemExit("No matching registered user")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
