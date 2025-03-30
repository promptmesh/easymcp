# Demo of how to use easymcp to perform RAG via mcp resources. Pair with a good filesystem mcp server to use your local documents dynamically.
# to run this example you need to install meilisearch python sdk, and run a meilisearch server on localhost:7700
# uv add easymcp meilisearch

import asyncio
import meilisearch.client 
from easymcp.client.ClientManager import ClientManager
from easymcp.client.transports.stdio import StdioServerParameters
from mcp.types import TextResourceContents
from itertools import count

# disable logging
from loguru import logger
logger.disable("easymcp")

# create a Meilisearch client
client = meilisearch.Client('http://127.0.0.1:7700')

# create an index
index = client.index('mcp-resources')

# create a ClientManager
mgr = ClientManager()

# define the servers
servers = {
    "timeserver": StdioServerParameters(
        command="uvx",
        args=["mcp-timeserver"]
    ),
    "llms-txt": StdioServerParameters(
        command="uvx",
        args=["mcp-llms-txt"]
    ),
}

async def main():
    # initialize the client manager and start the servers
    await mgr.init(servers)
    
    print("reading resources") # list resources
    resources = await mgr.list_resources()

    documents = []

    counter = count()

    print("indexing resources")
    for resource in resources:
        documents.append({
            "id": next(counter),
            "uri": str(resource.uri),
            "name": resource.name,
            "description": resource.description,
            "mime_type": resource.mimeType,
        })

    task = index.add_documents(documents) # add documents to the index
    index.wait_for_task(task.task_uid)

    print("indexing done")

    QUERY = "london"

    results = index.search(QUERY) # search for a resource
    hits = results.get("hits", [])

    print()

    for hit in hits:
        print(f"Result: {hit['name']}: {hit['uri']}")
        result = await mgr.read_resource(hit["uri"]) # resolve the resource uri

        for c in result.contents:
            if isinstance(c, TextResourceContents):
                print(c.text)

        print()

    print("done")

    await asyncio.Future()

asyncio.run(main())