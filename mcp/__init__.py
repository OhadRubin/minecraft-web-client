class ClientSession:
    def __init__(self, read=None, write=None):
        pass
    async def initialize(self):
        pass
    async def list_tools(self):
        return []
    async def call_tool(self, tool_name, arguments):
        return {"content": "", "status": "success"}

class StdioServerParameters:
    def __init__(self, command=None, args=None, env=None):
        self.command = command
        self.args = args
        self.env = env
