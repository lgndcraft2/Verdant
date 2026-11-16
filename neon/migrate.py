"""Apply the idempotent Neon schema and baseline seed. Requires DATABASE_URL."""
import asyncio
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv


async def main() -> None:
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env")
    database_url = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(database_url)
    try:
        async with conn.transaction():
            await conn.execute((root / "neon" / "schema.sql").read_text())
            await conn.execute((root / "neon" / "seed.sql").read_text().replace("public.fairness_baselines", "fairness_baselines"))
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
