#!/usr/bin/env python3
"""
Test script to verify the SDK fix using local source code.
Run with: python test_local.py
"""

import sys
import asyncio
from pathlib import Path

# Add local src directory to path (use local SDK, not installed package)
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from olakaisdk import olakai_config, olakai
from olakaisdk.shared.types import OlakaiEventParams


async def main():
    # Initialize SDK
    olakai_config(
        "136646d1-81fc-48f3-a796-9dbd1d603095",
        endpoint="http://localhost:3000",
        debug=True  # Set to True for development
    )

    # Create event params
    params = OlakaiEventParams(
        prompt="Write a product description for wireless headphones",
        response="Experience crystal-clear sound with our premium wireless headphones...",
        task="Content Generation",
        userEmail="walt.mann@gmail.com",
        tokens=150,
        chatId="cckej2lc40c0np1s3mcvef5ss",
        customData={
            "Department": "EMEA",
            "Location": "United Kingdom",
            "Feature": "Internal Processing",
            "TokensUsed": 150,
            "Rating": 2.5,
        },
    )

    # Send event - this should NOT raise "Olakai SDK not initialized" anymore
    olakai("event", "ai_activity", params)

    print("SUCCESS: Event sent without initialization error!")

    # Give async task time to complete
    await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
