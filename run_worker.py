"""Run the background transcription worker."""

import asyncio
from app.workers.worker import main


if __name__ == "__main__":
    asyncio.run(main())
