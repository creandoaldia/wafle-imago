# Wafle-Imago — Universal MCP Server for AI Image Generation

**Imago** (Latin: *image, likeness, representation*). From the root of "imagine" and "imagery".

Wafle-Imago turns words into images. A universal MCP server that works with **any MCP-compatible client** (OpenCode, Claude Desktop, Cursor, Windsurf, etc.). Supports multiple backends with automatic fallback, built-in security, and audit logging.

## Quick Start

```bash
pip install wafle-imago
wafle-imago --backend cloudflare
```

Requires Cloudflare or NVIDIA credentials in `.env` (see [Configuration](#configuration)).

## Backends

| Backend | Images | Cost | Auth | Limits |
|---------|--------|------|------|--------|
| **cloudflare** ✅ | FLUX.1 Schnell, SDXL, FLUX.2 Klein | **$0** | `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_API_TOKEN` | 10k neurons/day (~900 images) |
| **nvidia** ✅ | FLUX.1 Dev/Schnell, FLUX.2 Klein | **$0** | `NVIDIA_API_KEY` | 1k req/month |
| pollinations | ❌ Deprecated (HTTP 402) | — | — | — |
| hf | ⚠️ Credits depleted (resets monthly) | $0 | `HF_TOKEN` | Rate-limited |

## Configuration

### 1. Get Free Credentials

**Cloudflare Workers AI** (recommended — 900 images/day free):
1. Sign up at https://dash.cloudflare.com/sign-up/workers-and-pages (no credit card)
2. Go to Workers AI → "Use REST API" → copy Account ID + create API Token
3. Add to `.env`:
```bash
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_API_TOKEN=your_api_token
```

**NVIDIA NIM** (alternative — 1k req/month):
1. Sign up at https://build.nvidia.com (no credit card)
2. Get API key
3. Add to `.env`:
```bash
NVIDIA_API_KEY=nvapi-...
```

### 2. Add to MCP Client

```json
{
  "mcpServers": {
    "wafle-imago": {
      "command": ["wafle-imago", "--backend", "cloudflare"],
      "description": "AI image generation via Cloudflare Workers AI (free)"
    }
  }
}
```

### CLI Options

```bash
wafle-imago                          # MCP stdio mode (default: cloudflare)
wafle-imago --backend nvidia          # Use NVIDIA NIM backend
wafle-imago --http --port 8000       # HTTP SSE mode
wafle-imago --backend cloudflare     # Cloudflare Workers AI
wafle-imago --version                # Show version
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `generate_image` | Generate image from text prompt |
| `generate_video` | ❌ Not available on free backends |
| `list_models` | Available models with pricing |
| `get_balance` | Check auth status / backend mode |

## Security

- Prompt validation (NSFW, injection blocking)
- Rate limiting (configurable)
- Audit logging (JSONL)
- `safe` parameter for content safety

## Requirements

- Python 3.10+
- Windows, macOS, Linux
- One free Cloudflare or NVIDIA account

## Installation from Source

```bash
git clone https://github.com/creandoaldia/wafle-imago.git
cd wafle-imago
pip install -e .
```

## License

MIT
