# Cloudflare Worker: Cognitive Defense Gateway & C2PA Provenance Signer

This directory contains a Cloudflare Worker that acts as a cognitive defense gateway in front of LLM inference endpoints (via Cloudflare AI Gateway).

## Capabilities

1. **Multi-Turn Trajectory Embedding**: Uses Cloudflare Workers AI (`@cf/baai/bge-base-en-v1.5`) to embed conversational prompts in real-time.
2. **Stateful Evasion Penalty**: Evaluates session memory in KV/Vectorize to detect semantic rerouting (e.g. operators rephrasing refused requests as "objective comparisons" or "market rumors" in campaigns like GTG-84005 and GTG-04001).
3. **C2PA Provenance Signing**: Intercepts completions at the edge, computes SHA-256 digests via WebCrypto, and attaches authenticated C2PA v2.1 provenance headers.

## Local Development

```bash
npx wrangler dev
```
