# Wafle-Imago — Universal MCP Server for AI Image Generation

**Imago** (Latin: *image, likeness, representation*). From the root of "imagine" and "imagery".

Wafle-Imago turns words into images. A universal MCP server that works with **any MCP-compatible client** (OpenCode, Claude Desktop, Cursor, Windsurf, etc.). Supports multiple backends with automatic fallback, built-in security, and audit logging.

## Quick Start

```bash
pip install wafle-imago
wafle-imago
```

That's it. No API key, no registration, no configuration. Generates images in ~0.5s.

## Backends

| Backend | Images | Video | Audio | Auth Required | Cost |
|---------|--------|-------|-------|---------------|------|
| **pollinations** (anonymous) | ✅ | ❌ | ❌ | No | **$0, unlimited, no rate limit** |
| **pollinations** (with key) | ✅ | ✅ | ✅ | `POLLINATIONS_API_KEY` | From ~$0.001/gen |
| **hf** | ✅ | ❌ | ❌ | `HF_TOKEN` | $0 (rate-limited) |

## Configuration

### OpenCode / Claude Desktop / Cursor

Add to your MCP client config:

```json
{
  "mcpServers": {
    "wafle-imago": {
      "command": "wafle-imago",
      "description": "AI image generation — free, no auth, unlimited"
    }
  }
}
```

With API key for video/audio:

```json
{
  "mcpServers": {
    "wafle-imago": {
      "command": "wafle-imago",
      "env": {
        "POLLINATIONS_API_KEY": "sk_your_key_here"
      }
    }
  }
}
```

### CLI Options

```bash
wafle-imago                    # MCP stdio mode (default for agents)
wafle-imago --http --port 8000 # HTTP SSE mode
wafle-imago --backend hf       # Use HuggingFace backend
wafle-imago --version          # Show version
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `generate_image` | Generate image from text. Free, no auth needed |
| `generate_video` | Generate video (requires API key) |
| `list_models` | Available models with pricing |
| `get_balance` | Check auth status / mode |

## Security

- Prompt validation (NSFW, injection blocking)
- Rate limiting (configurable)
- Audit logging (JSONL)
- `safe` parameter for content safety

## Requirements

- Python 3.10+
- Windows, macOS, Linux

## Installation from Source

```bash
git clone https://github.com/creandoaldia/wafle-imago.git
cd wafle-imago
pip install -e .
```

## License

MIT

## Etymology

*Imago* (Latin) — image, likeness, representation. The root of "imagine", "imagery", and "imitation". From *imitari* (to copy, to represent). Wafle-Imago: the WAFLE ecosystem's engine for turning language into visual form.
