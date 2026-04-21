import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const server = new Server(
  {
    name: "opencode-bypass-v2",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "generate_image_v2",
      description: "Generate professional images using 2026 free bypass engine.",
      inputSchema: {
        type: "object",
        properties: {
          prompt: { type: "string", description: "Image prompt" },
          output_path: { type: "string", description: "Path to save image" }
        },
        required: ["prompt", "output_path"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "generate_image_v2") {
    const { prompt, output_path } = request.params.arguments;
    const scriptPath = path.join(path.dirname(new URL(import.meta.url).pathname), "scripts/bypass_engine.py");
    
    return new Promise((resolve) => {
      const py = spawn("python3", [scriptPath, prompt, output_path]);
      let output = "";
      py.stdout.on("data", (data) => output += data.toString());
      py.stderr.on("data", (data) => output += data.toString());
      
      py.on("close", (code) => {
        if (code === 0) {
          resolve({
            content: [{ type: "text", text: `Successfully generated image: ${output_path}` }],
          });
        } else {
          resolve({
            content: [{ type: "text", text: `Error generating image (code ${code}): ${output}` }],
            isError: true,
          });
        }
      });
    });
  }
  throw new Error("Tool not found");
});

const transport = new StdioServerTransport();
await server.connect(transport);
