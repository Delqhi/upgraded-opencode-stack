const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 7860;

// Agent name from env or default
const AGENT_NAME = process.env.AGENT_NAME || 'SIN-Agent';
const AGENT_DESCRIPTION = process.env.AGENT_DESCRIPTION || 'SIN A2A Agent';

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Health endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    agent: AGENT_NAME,
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0'
  });
});

// A2A Card endpoint
app.get('/.well-known/agent-card.json', (req, res) => {
  const cardPath = path.join(__dirname, '.well-known', 'agent-card.json');
  if (fs.existsSync(cardPath)) {
    res.json(JSON.parse(fs.readFileSync(cardPath, 'utf8')));
  } else {
    res.json({
      name: AGENT_NAME,
      description: AGENT_DESCRIPTION,
      url: `https://${process.env.SPACE_HOST || 'localhost'}/a2a/v1`,
      protocol: 'A2A',
      version: '1.0.0',
      capabilities: ['chat', 'task'],
      status: 'active'
    });
  }
});

// A2A v1 endpoint
app.post('/a2a/v1', async (req, res) => {
  try {
    const { action, params } = req.body;
    
    switch (action) {
      case 'agent.help':
        res.json({
          result: {
            name: AGENT_NAME,
            description: AGENT_DESCRIPTION,
            commands: ['help', 'health', 'status'],
            version: '1.0.0'
          }
        });
        break;
      
      case 'agent.health':
        res.json({
          result: {
            status: 'ok',
            agent: AGENT_NAME,
            uptime: process.uptime()
          }
        });
        break;
      
      case 'agent.card':
        res.json({
          result: {
            name: AGENT_NAME,
            description: AGENT_DESCRIPTION,
            protocol: 'A2A',
            version: '1.0.0'
          }
        });
        break;
      
      default:
        res.json({
          result: {
            message: `Unknown action: ${action}. Use 'agent.help' for available commands.`,
            agent: AGENT_NAME
          }
        });
    }
  } catch (error) {
    res.status(500).json({
      error: error.message,
      agent: AGENT_NAME
    });
  }
});

// A2A GET endpoint
app.get('/a2a/v1', (req, res) => {
  res.json({
    name: AGENT_NAME,
    description: AGENT_DESCRIPTION,
    protocol: 'A2A',
    version: '1.0.0',
    endpoints: {
      post: '/a2a/v1',
      card: '/.well-known/agent-card.json',
      health: '/health'
    }
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: AGENT_NAME,
    description: AGENT_DESCRIPTION,
    status: 'active',
    endpoints: {
      health: '/health',
      a2a: '/a2a/v1',
      card: '/.well-known/agent-card.json'
    }
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`${AGENT_NAME} listening on port ${PORT}`);
  console.log(`Health: http://localhost:${PORT}/health`);
  console.log(`A2A: http://localhost:${PORT}/a2a/v1`);
});
