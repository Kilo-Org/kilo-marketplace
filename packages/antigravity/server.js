import { spawn } from "child_process";
import * as path from "path";
import * as os from "os";
import * as fs from "fs";

function resolvePort() {
  const envVal = process.env.AGY_PROXY_PORT;
  if (envVal) {
    const parsed = parseInt(envVal, 10);
    if (Number.isInteger(parsed) && parsed > 0 && parsed <= 65535) {
      return parsed;
    }
  }
  return 52188;
}

const DEFAULT_PORT = resolvePort();

async function checkHealth(port, timeoutMs = 800) {
  try {
    const res = await fetch(`http://127.0.0.1:${port}/health`, { signal: AbortSignal.timeout(timeoutMs) });
    return res.ok;
  } catch {
    return false;
  }
}

export const AntigravityPlugin = async (_ctx) => {
  // Ensure the local bridge service is active
  let isHealthy = await checkHealth(DEFAULT_PORT, 1000);
  if (!isHealthy) {
    // If not running, start it via agy-proxy script if executable
    try {
      const proxyScript = path.join(os.homedir(), ".local", "bin", "agy-proxy");
      if (fs.existsSync(proxyScript)) {
        const child = spawn(proxyScript, ["start"], {
          detached: true,
          stdio: "ignore",
          env: { ...process.env, AGY_PROXY_PORT: String(DEFAULT_PORT) }
        });
        child.on("error", (err) => {
          console.warn("[kilo-plugin-antigravity] agy-proxy spawn error:", err);
        });
        child.unref();

        // Poll for proxy startup with timeout (up to 5 attempts, interval 300ms)
        for (let attempt = 0; attempt < 5; attempt++) {
          await new Promise((r) => setTimeout(r, 300));
          if (await checkHealth(DEFAULT_PORT, 500)) {
            isHealthy = true;
            break;
          }
        }
        if (!isHealthy) {
          console.warn(`[kilo-plugin-antigravity] agy-proxy started but did not respond on port ${DEFAULT_PORT} within timeout.`);
        }
      } else {
        console.warn(`[kilo-plugin-antigravity] agy-proxy script not found at ${proxyScript}. Please ensure the bridge is installed and running.`);
      }
    } catch (e) {
      console.warn("[kilo-plugin-antigravity] Failed to auto-start proxy:", e);
    }
  }

  return {
    async config(cfg) {
      cfg.provider = cfg.provider || {};
      cfg.provider["agy"] = {
        name: "Antigravity (AGY)",
        npm: "@ai-sdk/openai-compatible",
        options: {
          baseURL: `http://127.0.0.1:${DEFAULT_PORT}/v1`,
          apiKey: "agy-local"
        },
        models: {
          "gemini-4-argon": {
            name: "Gemini 4 Argon",
            reasoning: true,
            tool_call: true,
            cost: {
              input: 1.25,
              output: 5.0,
              cache_read: 0.3125
            },
            variants: {
              low: {},
              medium: {},
              high: {}
            },
            modalities: {
              input: ["text", "image"],
              output: ["text"]
            },
            limit: {
              context: 1000000,
              output: 65536
            }
          },
          "gemini-3.8-flash": {
            name: "Gemini 3.8 Flash",
            reasoning: true,
            tool_call: true,
            cost: {
              input: 0.15,
              output: 0.60,
              cache_read: 0.0375
            },
            variants: {
              low: {},
              medium: {},
              high: {}
            },
            modalities: {
              input: ["text", "image"],
              output: ["text"]
            },
            limit: {
              context: 1000000,
              output: 65536
            }
          },
          "claude-sonnet-5-5": {
            name: "Claude Sonnet 5.5",
            reasoning: true,
            tool_call: true,
            cost: {
              input: 3.0,
              output: 15.0,
              cache_read: 0.30,
              cache_write: 3.75
            },
            variants: {
              low: {},
              medium: {},
              high: {}
            },
            modalities: {
              input: ["text", "image"],
              output: ["text"]
            },
            limit: {
              context: 1000000,
              output: 65536
            }
          },
          "claude-opus-5-5": {
            name: "Claude Opus 5.5",
            reasoning: true,
            tool_call: true,
            cost: {
              input: 15.0,
              output: 75.0,
              cache_read: 1.50,
              cache_write: 18.75
            },
            variants: {
              low: {},
              medium: {},
              high: {}
            },
            modalities: {
              input: ["text", "image"],
              output: ["text"]
            },
            limit: {
              context: 1000000,
              output: 65536
            }
          },
          "gemini-2.5-flash-thinking": {
            name: "Gemini Flash Thinking",
            reasoning: true,
            tool_call: true,
            cost: {
              input: 0.15,
              output: 0.60,
              cache_read: 0.0375
            },
            modalities: {
              input: ["text", "image"],
              output: ["text"]
            },
            limit: {
              context: 1000000,
              output: 65536
            }
          },
          "gpt-oss-120b-medium": {
            name: "GPT-OSS 120B (Medium)",
            reasoning: true,
            tool_call: true,
            cost: {
              input: 0.50,
              output: 1.50
            },
            modalities: {
              input: ["text"],
              output: ["text"]
            },
            limit: {
              context: 131072,
              output: 32768
            }
          }
        }
      };
    }
  };
};

export const server = AntigravityPlugin;
export default { server: AntigravityPlugin };
