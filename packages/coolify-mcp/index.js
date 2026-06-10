#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const COOLIFY_URL = process.env.COOLIFY_URL;
const COOLIFY_API_TOKEN = process.env.COOLIFY_API_TOKEN;

if (!COOLIFY_URL || !COOLIFY_API_TOKEN) {
  console.error(
    "Missing required env vars: COOLIFY_URL and COOLIFY_API_TOKEN"
  );
  process.exit(1);
}

const BASE = `${COOLIFY_URL.replace(/\/$/, "")}/api/v1`;

async function api(path, { method = "GET", body, params } = {}) {
  let url = `${BASE}${path}`;
  if (params) {
    const qs = new URLSearchParams(params).toString();
    if (qs) url += `?${qs}`;
  }

  const opts = {
    method,
    headers: {
      Authorization: `Bearer ${COOLIFY_API_TOKEN}`,
      Accept: "application/json",
    },
  };

  if (body) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }

  const res = await fetch(url, opts);
  const text = await res.text();

  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = text;
  }

  if (!res.ok) {
    throw new Error(
      `Coolify API ${res.status}: ${typeof data === "string" ? data : JSON.stringify(data)}`
    );
  }

  return data;
}

function ok(data) {
  return {
    content: [
      {
        type: "text",
        text: typeof data === "string" ? data : JSON.stringify(data, null, 2),
      },
    ],
  };
}

function err(e) {
  return {
    content: [{ type: "text", text: `Error: ${e.message}` }],
    isError: true,
  };
}

// --- Server setup ---

const server = new McpServer({
  name: "coolify",
  version: "1.0.0",
});

// --- Health & Version ---

server.tool("coolify_healthcheck", "Verify connectivity to the Coolify API", {}, async () => {
  try {
    // Current API path is /health; older instances served /healthcheck.
    let data;
    try {
      data = await api("/health");
    } catch {
      data = await api("/healthcheck");
    }
    return ok({ status: "connected", response: data, url: COOLIFY_URL });
  } catch (e) {
    return err(e);
  }
});

server.tool("coolify_version", "Get the Coolify instance version", {}, async () => {
  try {
    return ok(await api("/version"));
  } catch (e) {
    return err(e);
  }
});

// --- Servers ---

server.tool(
  "coolify_list_servers",
  "List all servers managed by Coolify",
  {},
  async () => {
    try {
      return ok(await api("/servers"));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_get_server",
  "Get details for a specific server including resources and status",
  { uuid: z.string().describe("Server UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/servers/${uuid}`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_get_server_resources",
  "List all resources (apps, databases, services) on a server",
  { uuid: z.string().describe("Server UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/servers/${uuid}/resources`));
    } catch (e) {
      return err(e);
    }
  }
);

// --- Projects ---

server.tool(
  "coolify_list_projects",
  "List all projects",
  {},
  async () => {
    try {
      return ok(await api("/projects"));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_get_project",
  "Get project details including its environments",
  { uuid: z.string().describe("Project UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/projects/${uuid}`));
    } catch (e) {
      return err(e);
    }
  }
);

// --- Applications ---

server.tool(
  "coolify_list_applications",
  "List all applications across all projects",
  {},
  async () => {
    try {
      return ok(await api("/applications"));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_get_application",
  "Get full details for an application (config, status, env vars, domains)",
  { uuid: z.string().describe("Application UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/applications/${uuid}`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_start_application",
  "Start a stopped application",
  { uuid: z.string().describe("Application UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/applications/${uuid}/start`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_stop_application",
  "Stop a running application",
  { uuid: z.string().describe("Application UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/applications/${uuid}/stop`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_restart_application",
  "Restart an application (stop then start)",
  { uuid: z.string().describe("Application UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/applications/${uuid}/restart`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_get_application_logs",
  "Get recent container logs for a running application",
  {
    uuid: z.string().describe("Application UUID"),
    lines: z.number().optional().default(100).describe("Number of log lines to return (default 100)"),
  },
  async ({ uuid, lines }) => {
    try {
      return ok(await api(`/applications/${uuid}/logs`, { params: { lines: String(lines) } }));
    } catch (e) {
      return err(e);
    }
  }
);

// --- Deployments ---

server.tool(
  "coolify_deploy",
  "Trigger a deployment for one or more resources by UUID or tag. Returns deployment UUIDs for status tracking.",
  {
    uuid: z.string().optional().describe("Resource UUID(s), comma-separated for batch deploy"),
    tag: z.string().optional().describe("Tag name(s), comma-separated for batch deploy"),
    force: z.boolean().optional().default(false).describe("Force rebuild without cache"),
  },
  async ({ uuid, tag, force }) => {
    try {
      const params = {};
      if (uuid) params.uuid = uuid;
      if (tag) params.tag = tag;
      if (force) params.force = "true";
      return ok(await api("/deploy", { params }));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_get_deployment",
  "Get status and logs for a specific deployment",
  { uuid: z.string().describe("Deployment UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/deployments/${uuid}`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_cancel_deployment",
  "Cancel a queued or in-progress deployment",
  { uuid: z.string().describe("Deployment UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/deployments/${uuid}/cancel`, { method: "POST" }));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_list_running_deployments",
  "List all currently running deployments across the instance",
  {},
  async () => {
    try {
      return ok(await api("/deployments"));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_list_deployments",
  "List recent deployments for an application",
  {
    uuid: z.string().describe("Application UUID"),
    skip: z.number().optional().default(0).describe("Number of deployments to skip"),
    take: z.number().optional().default(10).describe("Number of deployments to return"),
  },
  async ({ uuid, skip, take }) => {
    try {
      return ok(
        await api(`/deployments/applications/${uuid}`, {
          params: { skip: String(skip), take: String(take) },
        })
      );
    } catch (e) {
      return err(e);
    }
  }
);

// --- Environment Variables ---

server.tool(
  "coolify_list_env_vars",
  "List all environment variables for an application",
  { uuid: z.string().describe("Application UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/applications/${uuid}/envs`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_create_env_var",
  "Create a new environment variable on an application. Changes take effect on the next deploy (coolify_deploy), not on restart.",
  {
    uuid: z.string().describe("Application UUID"),
    key: z.string().describe("Variable name"),
    value: z.string().describe("Variable value"),
    is_preview: z.boolean().optional().describe("Only for preview deployments"),
    is_literal: z.boolean().optional().describe("Treat value as literal (no escaping/interpolation)"),
    is_build_time: z
      .boolean()
      .optional()
      .describe("Available during build (older Coolify versions only; current versions unified build/runtime envs)"),
  },
  async ({ uuid, key, value, is_preview, is_literal, is_build_time }) => {
    try {
      const body = { key, value };
      if (is_preview !== undefined) body.is_preview = is_preview;
      if (is_literal !== undefined) body.is_literal = is_literal;
      if (is_build_time !== undefined) body.is_build_time = is_build_time;
      return ok(
        await api(`/applications/${uuid}/envs`, { method: "POST", body })
      );
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_update_env_var",
  "Update an existing environment variable on an application (matched by key). Changes take effect on the next deploy (coolify_deploy), not on restart.",
  {
    uuid: z.string().describe("Application UUID"),
    key: z.string().describe("Variable name to update"),
    value: z.string().describe("New value"),
    is_preview: z.boolean().optional().describe("Only for preview deployments"),
    is_literal: z.boolean().optional().describe("Treat value as literal (no escaping/interpolation)"),
  },
  async ({ uuid, key, value, is_preview, is_literal }) => {
    try {
      const body = { key, value };
      if (is_preview !== undefined) body.is_preview = is_preview;
      if (is_literal !== undefined) body.is_literal = is_literal;
      return ok(
        await api(`/applications/${uuid}/envs`, { method: "PATCH", body })
      );
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_delete_env_var",
  "Delete an environment variable from an application. Get the env var UUID from coolify_list_env_vars first.",
  {
    uuid: z.string().describe("Application UUID"),
    env_uuid: z.string().describe("Environment variable UUID (from coolify_list_env_vars)"),
  },
  async ({ uuid, env_uuid }) => {
    try {
      return ok(
        await api(`/applications/${uuid}/envs/${env_uuid}`, { method: "DELETE" })
      );
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_update_application",
  "Update application settings (image tag, branch, build pack, domains, etc.)",
  {
    uuid: z.string().describe("Application UUID"),
    settings: z
      .object({})
      .passthrough()
      .describe(
        "Key-value pairs to update. Common keys: docker_registry_image_tag, git_branch, build_pack, fqdn, ports_mappings, health_check_path"
      ),
  },
  async ({ uuid, settings }) => {
    try {
      return ok(await api(`/applications/${uuid}`, { method: "PATCH", body: settings }));
    } catch (e) {
      return err(e);
    }
  }
);

// --- Databases ---

server.tool(
  "coolify_list_databases",
  "List all databases managed by Coolify",
  {},
  async () => {
    try {
      return ok(await api("/databases"));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_get_database",
  "Get details for a specific database",
  { uuid: z.string().describe("Database UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/databases/${uuid}`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_start_database",
  "Start a stopped database",
  { uuid: z.string().describe("Database UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/databases/${uuid}/start`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_stop_database",
  "Stop a running database",
  { uuid: z.string().describe("Database UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/databases/${uuid}/stop`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_restart_database",
  "Restart a database",
  { uuid: z.string().describe("Database UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/databases/${uuid}/restart`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_list_database_backups",
  "List scheduled backup configurations for a database",
  { uuid: z.string().describe("Database UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/databases/${uuid}/backups`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_list_backup_executions",
  "List execution history (runs, status, size) for a scheduled database backup",
  {
    uuid: z.string().describe("Database UUID"),
    scheduled_backup_uuid: z.string().describe("Scheduled backup UUID (from coolify_list_database_backups)"),
  },
  async ({ uuid, scheduled_backup_uuid }) => {
    try {
      return ok(
        await api(`/databases/${uuid}/backups/${scheduled_backup_uuid}/executions`)
      );
    } catch (e) {
      return err(e);
    }
  }
);

// --- Services ---

server.tool(
  "coolify_list_services",
  "List all one-click services deployed in Coolify",
  {},
  async () => {
    try {
      return ok(await api("/services"));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_get_service",
  "Get details for a specific service",
  { uuid: z.string().describe("Service UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/services/${uuid}`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_start_service",
  "Start a stopped one-click service",
  { uuid: z.string().describe("Service UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/services/${uuid}/start`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_stop_service",
  "Stop a running one-click service",
  { uuid: z.string().describe("Service UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/services/${uuid}/stop`));
    } catch (e) {
      return err(e);
    }
  }
);

server.tool(
  "coolify_restart_service",
  "Restart a one-click service",
  { uuid: z.string().describe("Service UUID") },
  async ({ uuid }) => {
    try {
      return ok(await api(`/services/${uuid}/restart`));
    } catch (e) {
      return err(e);
    }
  }
);

// --- Resources (all) ---

server.tool(
  "coolify_list_all_resources",
  "List all resources across all servers (applications, databases, services)",
  {},
  async () => {
    try {
      return ok(await api("/resources"));
    } catch (e) {
      return err(e);
    }
  }
);

// --- Start ---

const transport = new StdioServerTransport();
await server.connect(transport);
