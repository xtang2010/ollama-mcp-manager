# ollama-mcp-manager

With so many MCP servers out there, each have tens of tools, to load all of them to LLM seems a waste, and sometime confuse the LLM.

This tool allows you connect to MCP servers while you wish, and pull only tools related only to the server of it. So if you have more percise control of what MCP Servers to use.

## How to use

Check the sample code below. Basically `add_server()` to connect to a MCP Server, and `remove_server()` to disconnect to a MCP Server. 

```
import os
import asyncio

# MCP Servers to connect to
server_params_list = {
    "filesystem" : StdioServerParameters(
        command="npx", 
        args=["-y", "@modelcontextprotocol/server-filesystem", os.getcwd()],
        env=None
    ),
    "excel" : SseServerParameters(url="http://localhost:8000/sse")
}

async def run():
    from ollama_mcp import OllamaMcp

    omcp = OllamaMcp()
    for server in server_params_list:
        await omcp.add_server(server, server_params_list[server])
    print(f"Total {len(omcp.list_tools())} tools exist")

    await omcp.remove_server("filesystem")
    print(f"After remove filesystem, {len(omcp.list_tools())} tools exist")

    await omcp.close()
    print(f"After close, {len(omcp.list_tools())} tools exist")

if __name__ == "__main__":
    asyncio.run(run())
```

## Ollama consideration

To help deal with Ollama, `ollama_tools()` is provided, it will conveft MCP "list_tools()" output to Ollama "tool" list, so you can:

```
otools = omcp.ollama_tools("excel")
ollama.chat("llama3.2", messages, tools = otools)
```

## Tool consideration
You can even provide the `add_server()`, `remove_server()` as tools to LLM, with a list of server description. So they will be connected necessary MCP Server before they request the services.

## Work around
This code use ClientSessionGroup in MCP Python-sdk. Due to some issue (https://github.com/modelcontextprotocol/python-sdk/issues/922) in the sdk, currently there are additional code to workaround the issue. Once the issue solved, these workaround can be moved.



