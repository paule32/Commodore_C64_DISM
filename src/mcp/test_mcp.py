import asyncio

from mcp import Client


async def main():
    async with Client(
        "http://servera:8000/mcp"
    ) as client:

        tools = await client.list_tools()

        print("Verfügbare Tools:")

        for tool in tools.tools:
            print(" -", tool.name)


if __name__ == "__main__":
    asyncio.run(main())
