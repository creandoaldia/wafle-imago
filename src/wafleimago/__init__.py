"""Wafle-Imago — universal MCP server for AI image generation.

Imago (Latin): image, likeness, representation.
From the root of "imagine", "imagery" — turning words into images.

Wafle-Imago is the WAFLE ecosystem's image generation engine.

Backends (free, no credit card required):
  - cloudflare (10k neurons/day, ~900 images via FLUX/SDXL) — RECOMMENDED
  - nvidia (1k req/month, FLUX/SDXL/SANA via NVIDIA NIM)
  
Legacy backends (may require payment):
  - hf (HuggingFace Inference Providers, requires HF_TOKEN with credits)
  - pollinations (anonymous, deprecated — requires POLLINATIONS_API_KEY)
"""

__version__ = "0.1.0"
