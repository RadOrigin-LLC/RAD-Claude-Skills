---
name: map
description: >
  Generate a self-contained HTML graph of an OKF knowledge bundle (no
  dependencies, opens in a browser). Use when the user says "visualize my
  knowledge base", "show me the map", "map my OKF bundle", or wants to see
  how concepts connect.
argument-hint: "<path-to-bundle>"
user-invocable: true
allowed-tools: Bash Read
---

# rad-okf: map

1. Determine the bundle path.
2. Run: `python "${CLAUDE_PLUGIN_ROOT}/scripts/okf_map.py" <path> --name "<bundle name>"`
3. Report the output file path and tell the user they can open it by double-clicking. Offer to open it (`Start-Process <file>` on Windows) if they want.

This only writes `viz.html` (an output artifact); it never modifies knowledge files.
