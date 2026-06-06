# @radoriginllc/coolify-mcp

MCP server wrapping the [Coolify](https://coolify.io) REST API. Manage deployments, applications, databases, services, and infrastructure from Claude Code or any MCP-compatible client.

## Quick Start

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "coolify": {
      "command": "npx",
      "args": ["-y", "@radoriginllc/coolify-mcp"],
      "env": {
        "COOLIFY_URL": "https://your-coolify-instance.example.com",
        "COOLIFY_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

Or run directly:

```bash
COOLIFY_URL=https://coolify.example.com COOLIFY_API_TOKEN=your-token npx @radoriginllc/coolify-mcp
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `COOLIFY_URL` | Yes | Base URL of your Coolify instance (e.g., `https://coolify.example.com`) |
| `COOLIFY_API_TOKEN` | Yes | API token from Coolify Settings > API Tokens |

## Tools

### Health & Version
| Tool | Description |
|------|-------------|
| `coolify_healthcheck` | Verify connectivity to the Coolify API |
| `coolify_version` | Get the Coolify instance version |

### Servers
| Tool | Description |
|------|-------------|
| `coolify_list_servers` | List all servers managed by Coolify |
| `coolify_get_server` | Get details for a specific server |
| `coolify_get_server_resources` | List all resources on a server |

### Projects
| Tool | Description |
|------|-------------|
| `coolify_list_projects` | List all projects |
| `coolify_get_project` | Get project details including environments |

### Applications
| Tool | Description |
|------|-------------|
| `coolify_list_applications` | List all applications |
| `coolify_get_application` | Get full application details |
| `coolify_start_application` | Start a stopped application |
| `coolify_stop_application` | Stop a running application |
| `coolify_restart_application` | Restart an application |
| `coolify_get_application_logs` | Get recent container logs |
| `coolify_update_application` | Update application settings |

### Deployments
| Tool | Description |
|------|-------------|
| `coolify_deploy` | Trigger a deployment by UUID or tag |
| `coolify_get_deployment` | Get deployment status and logs |
| `coolify_list_deployments` | List recent deployments for an application |

### Environment Variables
| Tool | Description |
|------|-------------|
| `coolify_list_env_vars` | List environment variables for an application |
| `coolify_create_env_var` | Create a new environment variable |

### Databases
| Tool | Description |
|------|-------------|
| `coolify_list_databases` | List all databases |
| `coolify_get_database` | Get database details |
| `coolify_start_database` | Start a stopped database |
| `coolify_stop_database` | Stop a running database |
| `coolify_restart_database` | Restart a database |

### Services
| Tool | Description |
|------|-------------|
| `coolify_list_services` | List all one-click services |
| `coolify_get_service` | Get service details |

### Resources
| Tool | Description |
|------|-------------|
| `coolify_list_all_resources` | List all resources across all servers |

## Companion Plugin

For Coolify deployment patterns, troubleshooting guides, and an AI reviewer agent, install [rad-coolify-orchestrator](https://github.com/RadOrigin-LLC/RAD-Claude-Skills/tree/main/plugins/rad-coolify-orchestrator) — it pairs with this MCP server to give Claude deep Coolify knowledge alongside the operational tools.

## Requirements

- Node.js >= 18
- A running Coolify v4 instance with API access enabled

## License

Apache-2.0
