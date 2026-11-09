import { spawn } from "child_process";
import * as path from "path";
import * as os from "os";

const DEFAULT_PORT = 52188;

export const AntigravityPlugin = async (_ctx) => {
  // Ensure the local bridge service is active
  try {
    const res = await fetch(`http://127.0.0.1:${DEFAULT_PORT}/health`, { signal: AbortSignal.timeout(1000) });
    if (!res.ok) {
      throw new Error(`Health check returned status ${res.status}`);
    }
  } catch {
    // If not running, start it via agy-proxy script or launchctl
    try {
      const proxyScript = path.join(os.homedir(), ".local", "bin", "agy-proxy");
      const child = spawn(proxyScript, ["start"], { detached: true, stdio: "ignore" });
      child.unref();
      // Wait a moment for startup
      await new Promise((r) => setTimeout(r, 1200));
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
              cache_read: 0.30
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
              cache_read: 1.50
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
              input: ["text", "image"],
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
