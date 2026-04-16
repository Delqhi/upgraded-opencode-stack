#!/usr/bin/env node
/**
 * NVIDIA NIM Proxy for OpenCode
 * 
 * Converts OpenAI Responses API (/v1/responses) to Chat Completions API (/v1/chat/completions).
 * OpenCode 1.3.10 uses the Vercel AI SDK which defaults to /v1/responses, but NVIDIA NIM
 * only supports /v1/chat/completions. This proxy translates in between.
 * 
 * Usage: NVIDIA_API_KEY=your_key node nvidia-proxy.js
 * Then set provider baseURL to http://127.0.0.1:4199/v1
 */

const http = require('http');

const PORT = process.env.PORT || 4199;
const API_KEY = process.env.NVIDIA_API_KEY;
const TARGET = 'https://integrate.api.nvidia.com/v1';

if (!API_KEY) {
  console.error('ERROR: NVIDIA_API_KEY environment variable is required');
  process.exit(1);
}

console.log(`[NVIDIA-Proxy] Starting on port ${PORT} → ${TARGET}`);

function convertRequest(body) {
  try {
    const data = JSON.parse(body);
    
    // Map Responses API to Chat Completions API
    const chat = {
      model: data.model,
      messages: data.input || data.messages || [{ role: 'user', content: '' }],
      stream: data.stream !== undefined ? data.stream : true,
    };
    
    // Optional parameters
    if (data.temperature !== undefined) chat.temperature = data.temperature;
    if (data.max_tokens !== undefined) chat.max_tokens = data.max_tokens;
    if (data.max_output_tokens !== undefined) chat.max_tokens = data.max_output_tokens;
    if (data.top_p !== undefined) chat.top_p = data.top_p;
    if (data.stop !== undefined) chat.stop = data.stop;
    if (data.seed !== undefined) chat.seed = data.seed;
    if (data.n !== undefined) chat.n = data.n;
    
    return JSON.stringify(chat);
  } catch (e) {
    return body; // Pass through if not JSON
  }
}

http.createServer((req, res) => {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', () => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    let targetUrl = `${TARGET}${url.pathname}`;
    
    // If request is to /v1/responses, rewrite to /v1/chat/completions
    if (req.method === 'POST' && url.pathname.includes('/responses')) {
      targetUrl = targetUrl.replace('/responses', '/chat/completions');
      body = convertRequest(body);
      console.log(`[NVIDIA-Proxy] ${req.method} ${url.pathname} → /chat/completions`);
    } else {
      console.log(`[NVIDIA-Proxy] ${req.method} ${url.pathname}`);
    }
    
    const proxyOptions = {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
        'Accept': 'application/json',
      },
    };
    
    const proxy = http.request(targetUrl, proxyOptions, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.on('data', chunk => res.write(chunk));
      proxyRes.on('end', () => res.end());
    });
    
    proxy.on('error', (err) => {
      console.error('[NVIDIA-Proxy] Error:', err.message);
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: { message: `Proxy error: ${err.message}` } }));
    });
    
    proxy.write(body);
    proxy.end();
  });
}).listen(PORT, '127.0.0.1', () => {
  console.log(`[NVIDIA-Proxy] Ready at http://127.0.0.1:${PORT}/v1`);
  console.log('[NVIDIA-Proxy] Configure OpenCode provider baseURL to: http://127.0.0.1:4199/v1');
});
