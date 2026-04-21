import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fetch from "node-fetch-native";
import fs from "fs";
import path from "path";

const server = new Server(
  {
    name: "opencode-flux-bypass",
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
      name: "generate_image_flux",
      description: "Generate high-quality images using Flux 1.1 (Free Bypass).",
      inputSchema: {
        type: "object",
        properties: {
          prompt: { type: "string", description: "Image prompt" },
          output_path: { type: "string", description: "Path to save image" },
          aspect_ratio: { type: "string", enum: ["1:1", "16:9", "9:16"], default: "1:1" }
        },
        required: ["prompt", "output_path"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "generate_image_flux") {
    const { prompt, output_path, aspect_ratio } = request.params.arguments;
    
    try {
      const res = await fetch("https://fluximagegen.com/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, style: "photorealism" })
      });
      
      const data = await res.json();
      if (!data.imageUrl) throw new Error("No image URL in response");
      
      const imgRes = await fetch(data.imageUrl);
      const buffer = await imgRes.arrayBuffer();
      
      const fullPath = path.resolve(output_path);
      fs.mkdirSync(path.dirname(fullPath), { recursive: true });
      fs.writeFileSync(fullPath, Buffer.from(buffer));
      
      return {
        content: [{ type: "text", text: `Successfully generated image and saved to ${fullPath}` }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
        isError: true,
      };
    }
  }
  throw new Error("Tool not found");
});

const transport = new StdioServerTransport();
await server.connect(transport);
