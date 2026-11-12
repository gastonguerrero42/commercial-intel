from crewai.tools import BaseTool
import os, asyncio
MCP_ROOT=os.getenv('MCP_FILESYSTEM_ROOT','./data/docs')
async def _mcp_list():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params=StdioServerParameters(command='npx', args=['-y','@modelcontextprotocol/server-filesystem', MCP_ROOT])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize(); tools=await s.list_tools(); return [t.name for t in tools.tools]
class MCPDriveTool(BaseTool):
    name: str='mcp_drive_reader'; description: str='List files via MCP Filesystem.'
    def _run(self, query: str) -> str:
        try:
            tools=asyncio.run(_mcp_list()); files=os.listdir(MCP_ROOT) if os.path.exists(MCP_ROOT) else []
            return f'[MCP REAL] Tools: {tools}. Files: {files}'
        except Exception as e: return f'[MCP FALLBACK: {e}] Local files: {os.listdir(MCP_ROOT) if os.path.exists(MCP_ROOT) else []}'
class MCPWebTool(BaseTool):
    name: str='mcp_web_search'; description: str='Search web via MCP Fetch.'
    def _run(self, query: str) -> str:
        try:
            import httpx; r=httpx.get(f'https://html.duckduckgo.com/html/?q={query}', headers={'User-Agent':'Mozilla/5.0'}, timeout=10)
            return f'[MCP Fetch Fallback] Status {r.status_code} for {query}. For Brave MCP set BRAVE_API_KEY.'
        except Exception as e: return f'[MCP Web Error] {e}'
