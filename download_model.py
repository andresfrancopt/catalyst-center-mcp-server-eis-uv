#!/usr/bin/env python3
"""
Download a sentence-transformer model into this repo's local cache.

This script is a one-time setup step required before running the MCP server.
The MCP server uses a local sentence-transformer model (all-MiniLM-L6-v2) to
perform cosine similarity search over the Catalyst Center Swagger API spec,
enabling natural language endpoint discovery. The model must be available
locally because the server runs in fully offline mode (TRANSFORMERS_OFFLINE=1).

Usage
-----
Standard download:
    python download_model.py

On networks with SSL inspection (corporate proxies that re-sign TLS traffic):
    python download_model.py --no-ssl-verify

The --no-xet flag is enabled by default and disables HuggingFace's XetHub
chunked download protocol, which can cause 'Byte range not sequential' errors
on some networks. You can explicitly toggle it:
    python download_model.py --no-ssl-verify --no-xet   # explicitly on (default)
    python download_model.py --no-ssl-verify --no-no-xet # disable the flag

After a successful run the model will be saved to:
    embeddings_cache/model/all-MiniLM-L6-v2/

The MCP server will load from that path automatically on startup.
"""

import argparse
import os
from pathlib import Path


def _disable_ssl_verification():
    """Patch Python's SSL and httpx to skip certificate verification.
    Required on networks with SSL inspection (e.g. corporate proxies)."""
    import ssl
    import httpx

    ssl._create_default_https_context = ssl._create_unverified_context
    os.environ["CURL_CA_BUNDLE"] = ""
    os.environ["REQUESTS_CA_BUNDLE"] = ""

    # Patch httpx to use a no-verify client by default
    _original_init = httpx.Client.__init__

    def _patched_init(self, *args, **kwargs):
        kwargs.setdefault("verify", False)
        _original_init(self, *args, **kwargs)

    httpx.Client.__init__ = _patched_init

    _original_async_init = httpx.AsyncClient.__init__

    def _patched_async_init(self, *args, **kwargs):
        kwargs.setdefault("verify", False)
        _original_async_init(self, *args, **kwargs)

    httpx.AsyncClient.__init__ = _patched_async_init
    print("Warning: SSL verification disabled.")


def _disable_xet():
    """Disable HuggingFace XetHub chunked download protocol.
    Required when xet downloads fail with 'Byte range not sequential' errors."""
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    print("Warning: XetHub download protocol disabled, falling back to standard HTTP download.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download local sentence-transformer model cache")
    parser.add_argument("--model-name", default="all-MiniLM-L6-v2", help="SentenceTransformer model name")
    parser.add_argument(
        "--base-dir",
        default=str(Path(__file__).resolve().parent / "embeddings_cache"),
        help="Base cache directory (default: ./embeddings_cache)",
    )
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        help="Disable SSL certificate verification (use on networks with SSL inspection)",
    )
    parser.add_argument(
        "--no-xet",
        action="store_true",
        default=True,
        help="Disable XetHub chunked download protocol (default: True; use if you see 'Byte range not sequential' errors)",
    )
    args = parser.parse_args()

    if args.no_xet:
        _disable_xet()

    if args.no_ssl_verify:
        _disable_ssl_verification()

    # Import after potential SSL patch
    from sentence_transformers import SentenceTransformer

    model_dir = Path(args.base_dir).expanduser().resolve() / "model" / args.model_name
    model_dir.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading/loading model '{args.model_name}' into: {model_dir}")
    model = SentenceTransformer(args.model_name)
    model.save(str(model_dir))
    print("Model saved locally.")


if __name__ == "__main__":
    main()

