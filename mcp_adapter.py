import asyncio
import json
from typing import List, Dict, Any
from langchain.tools import tool

class McpAdapter:
    def __init__(self, process, reader, writer):
        self.process = process
        self.reader = reader
        self.writer = writer
        self.tools = []

    @classmethod
    async def from_command(cls, command: str):
        process = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE
        )
        return cls(process, process.stdout, process.stdin)

    async def initialize(self):
        self.writer.write((json.dumps({"type": "list_tools"}) + "\n").encode())
        await self.writer.drain()

        line = await self.reader.readline()
        data = json.loads(line.decode())

        if data["type"] == "tool_list":
            self.tools = [self._wrap_tool(t) for t in data["tools"]]

    def _wrap_tool(self, tool_def: Dict[str, Any]):
        name = tool_def["name"]
        description = tool_def["description"]
        parameters = tool_def.get("parameters", {})

        @tool(name=name, description=description, args_schema=None)
        def remote_tool(**kwargs):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._call_tool(name, kwargs))

        return remote_tool

    async def _call_tool(self, tool_name: str, args: dict) -> str:
        request = {
            "type": "call_tool",
            "tool_name": tool_name,
            "args": args
        }
        self.writer.write((json.dumps(request) + "\n").encode())
        await self.writer.drain()

        line = await self.reader.readline()
        response = json.loads(line.decode())

        return response.get("output", "")

    async def get_tools(self):
        return self.tools

    async def close(self):
        self.process.terminate()
        await self.process.wait()
