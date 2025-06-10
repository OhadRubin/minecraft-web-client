Title: mcp-client

URL Source: https://www.npmjs.com/package/mcp-client/v/1.8.0

Markdown Content:
1.8.0•Public•Published 3 months ago

*   [Readme](https://www.npmjs.com/package/mcp-client/v/1.8.0?activeTab=readme)
*   [Code Beta](https://www.npmjs.com/package/mcp-client/v/1.8.0?activeTab=code)
*   [4 Dependencies](https://www.npmjs.com/package/mcp-client/v/1.8.0?activeTab=dependencies)
*   [9 Dependents](https://www.npmjs.com/package/mcp-client/v/1.8.0?activeTab=dependents)
*   [17 Versions](https://www.npmjs.com/package/mcp-client/v/1.8.0?activeTab=versions)

An [MCP](https://glama.ai/blog/2024-11-25-model-context-protocol-quickstart) client for Node.js.

> [!TIP] This client has been tested with [FastMCP](https://github.com/punkpeye/fastmcp).

[MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk) provides a client for the MCP protocol, but it's a little verbose for my taste. This client abstracts away some of the lower-level details and provides a more convenient API.

import { MCPClient } from "mcp-client";

const client = new MCPClient({
  name: "Test",
  version: "1.0.0",
});

await client.connect({
  sseUrl: "http://localhost:8080/sse",
});

await client.ping();

const result = await client.callTool({
  name: "add",
  arguments: { a: 1, b: 2 },
});

const result = await client.callTool(
  {
    name: "add",
    arguments: { a: 1, b: 2 },
  },
  {
    resultSchema: z.object({
      content: z.array(
        z.object({
          type: z.literal("text"),
          text: z.string(),
        }),
      ),
    }),
  },
);

const tools = await client.getAllTools();

const resources = await client.getAllResources();

const resource = await client.getResource({ uri: "file:///logs/app.log" });

await client.setLoggingLevel("debug");

client.on("loggingMessage", (message) => {
  console.log(message);
});

> [!NOTE] Equivalent to `setNotificationHandler(LoggingMessageNotificationSchema, (message) => { ... })` in the MCP TypeScript SDK.

Package Sidebar
---------------

### Install

`npm i mcp-client@1.8.0`

### Version

1.8.0

### License

MIT

### Unpacked Size

37.1 kB

### Total Files

13

### Last publish

a month ago

### Collaborators

*   [![Image 1: punkpeye](https://www.npmjs.com/npm-avatar/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdmF0YXJVUkwiOiJodHRwczovL3MuZ3JhdmF0YXIuY29tL2F2YXRhci9kMjU3NDU0MDBkZDliMWI5ZjE0MWFjYzFmNzU0M2Y2Yj9zaXplPTEwMCZkZWZhdWx0PXJldHJvIn0.T14Ofla7fzdUDhNeVH9-I1iuCnV5i5TST_OoNWUWp6w)](https://www.npmjs.com/~punkpeye)

[**Try** on RunKit](https://runkit.com/npm/mcp-client)

[**Report** malware](https://www.npmjs.com/support?inquire=security&security-inquire=malware&package=mcp-client&version=1.8.0)