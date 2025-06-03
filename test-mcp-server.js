#!/usr/bin/env node

/**
 * Simple test script to verify the Minecraft MCP server is working
 * This script tests the connection and lists available tools
 */

import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";

const PORT = process.env.PORT || 4000;
const SERVER_URL = `http://localhost:${PORT}/stream`;

async function testMCPServer() {
    console.log(`Testing Minecraft MCP Server at ${SERVER_URL}`);

    try {
        // Create MCP client
        const client = new Client({
            name: "test-client",
            version: "1.0.0",
        }, {
            capabilities: {},
        });

        // Create HTTP streaming transport
        const transport = new StreamableHTTPClientTransport(
            new URL(SERVER_URL)
        );

        console.log("Connecting to MCP server...");
        await client.connect(transport);

        console.log("✅ Successfully connected to MCP server!");

        // List available tools
        console.log("\n📋 Available tools:");
        const toolsResult = await client.listTools();

        if (toolsResult.tools && toolsResult.tools.length > 0) {
            toolsResult.tools.forEach((tool, index) => {
                console.log(`${index + 1}. ${tool.name} - ${tool.description}`);
            });

            console.log(`\n🎉 Found ${toolsResult.tools.length} available tools!`);
        } else {
            console.log("❌ No tools found");
        }

        // Test connection status tool
        console.log("\n🔍 Testing connectionStatus tool...");
        try {
            const result = await client.callTool({
                name: "connectionStatus",
                arguments: {}
            });

            console.log("✅ connectionStatus result:", result.content);
        } catch (error) {
            console.log("❌ connectionStatus failed:", error.message);
        }

        // Close connection
        await client.close();
        console.log("\n✅ Test completed successfully!");

    } catch (error) {
        console.error("❌ Test failed:", error.message);
        console.error("\nMake sure the MCP server is running with:");
        console.error(`  PORT=${PORT} pnpm mcp-server`);
        process.exit(1);
    }
}

// Run the test
testMCPServer().catch(console.error);