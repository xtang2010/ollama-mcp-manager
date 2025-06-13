import asyncio, anyio
from mcp.client.stdio import StdioServerParameters
from mcp.client.session_group import ClientSessionGroup, SseServerParameters, StreamableHttpParameters
import json

class OllamaMcp:
    def __init__(self, config = None):
        self.group = ClientSessionGroup()
        self.mcpServers = {}
        self.mcpSessions = []
        if (config):
            self.load_config(config)
    
    def load_config(self, config):
        with open(config) as fp:
            o = json.load(fp)
        if "mcpServers" in o:
            for server in o['mcpServers']:
                args = o['mcpServers'][server]
                if ('command' in args):
                    sparam = StdioServerParameters(**args)
                elif ('url' in args):
                    if ('terminate_on_close' in args):
                        sparam = StreamableHttpParameters(**args)
                    else:
                        sparam = SseServerParameters(**args)   
                else:
                    print(f"Can not guess Server '{server}' with '{args}', ignored.")
                    continue
                self.mcpServers[server] = sparam

    def list_servers(self):
        return [s for s in self.mcpServers]

    async def add_server(self, server_name, server_param = None):
        for ms in self.mcpSessions:
            if ms['name'] == server_name:
                if ms['connected'] == False:
                    session = ms['session']
                    result = await session.initialize()
                    self.group._session_exit_stacks[session]=ms['exit_stack']
                    await self.group._aggregate_components(result.serverInfo, session)
                    ms['connected'] = True
                return ms['session']

        if server_name not in self.mcpServers:
            if (server_param is None):
                return None
            self.mcpServers[server_name] = server_param
        else:
            if server_param:
                self.mcpServers[server_name] = server_param
            else:
                server_param = self.mcpServers[server_name]

        ms = {}
        ms['name'] = server_name
        ms['session'] = await self.group.connect_to_server(server_param)
        ms['connected'] = True   
        self._current_session = None     
        self.mcpSessions.append(ms)
        return ms['session']
    
    async def remove_server(self, server_name):
        for ms in self.mcpSessions:
            if ms['name'] == server_name:
                if ms['connected']:
                    ms['connected'] = False
                    ms['exit_stack'] = self.group._session_exit_stacks.pop(ms['session'])
                    await self.group.disconnect_from_server(ms['session'])
                break
        
        while (len(self.mcpSessions) > 0 and self.mcpSessions[-1]['connected'] == False):
            ms = self.mcpSessions.pop()
            await ms['exit_stack'].aclose()

    def group_session(self):
        return self.group
    
    def list_tools(self, server=None):
        if server is not None:
            if server not in self.mcpSessions:
                return {}
            session = self.mcpSessions[server]
            tool_names = self.group._sessions[session].tools
            mtools = {x : self.group._tools[x] for x in tool_names}
        else:
            mtools = self.group._tools
        return mtools
    
    def ollama_tools(self, server = None):

        otools = []
        mtools = self.list_tools(server)
        for mname, mtool in mtools.items():        
            otool = {}
            otool['type'] = 'function'
            otool['function'] = {}
            otool['function']['name'] = mname
            otool['function']['description'] = mtool.description
            param = mtool.inputSchema
            try:
                param.pop('$schema')
                param.pop('additionalProperties')
            except:
                pass
            otool['function']['parameters'] = param
            otools.append(otool)
    
        return otools
    
    def call_tool(self, tool_name, tool_args):
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.group.call_tool(tool_name, tool_args))
        return result

    async def close(self):
        for ms in reversed(self.mcpSessions):
            if (ms['connected'] == False):
                await ms['exit_stack'].aclose()
            else:
                await self.group.disconnect_from_server(ms['session'])
        self.mcpSessions = []
