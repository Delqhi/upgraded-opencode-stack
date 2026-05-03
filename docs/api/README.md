# API Documentation

## OpenAPI/Swagger Specification

The Code-Swarm API follows OpenAPI 3.0 standards.

### FastAPI Endpoints

```yaml
openapi: 3.0.2
info:
  title: Code-Swarm API
  description: SOTA Agent Swarm API with FastAPI + gRPC
  version: 1.0.0
servers:
  - url: https://api.opensin.ai
    description: Production server
  - url: http://localhost:8000
    description: Development server
paths:
  /health:
    get:
      summary: Health check
      responses:
        '200':
          description: Service is healthy
  /agents:
    get:
      summary: List all agents
      responses:
        '200':
          description: List of agents
  /tasks:
    get:
      summary: List all tasks
      responses:
        '200':
          description: List of tasks
components:
  securitySchemes:
    JWT:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

### Authentication

- **JWT Bearer Token** required for all endpoints except `/health`
- **Rate Limiting**: 1000 requests/hour
- **CORS**: Configured via `ALLOWED_ORIGINS` environment variable

### API Clients

```bash
# Python client example
import requests

response = requests.get(
    "https://api.opensin.ai/agents",
    headers={"Authorization": "Bearer YOUR_JWT_TOKEN"}
)
print(response.json())
```

## Swagger UI

Access the interactive Swagger UI at:

```
# Development
http://localhost:8000/docs

# Production
https://api.opensin.ai/docs
```

![Swagger UI Screenshot](https://fastapi.tiangolo.com/img/tutorial/first-steps/image03.png)

## ReDoc

Alternative documentation at:

```
# Development
http://localhost:8000/redoc

# Production
https://api.opensin.ai/redoc
```
