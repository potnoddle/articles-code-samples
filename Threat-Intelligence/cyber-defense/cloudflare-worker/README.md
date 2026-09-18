# Cloudflare Worker: Edge Capability Token Validator & Honey-Router

This directory contains a production Cloudflare Worker implementing edge-level Principle of Least Authority (PoLA) capability token validation and automated honey-routing against high-speed cloud harvesting campaigns (such as GTG-50014).

## Architecture

```
[Inbound Request] ──> [Cloudflare Edge (V8 Isolate)]
                            │
              ┌─────────────┴─────────────┐
              │ HMAC-SHA256 Sig Check     │ (<1ms WebCrypto)
              │ TTL Expiration Check (15m)│
              │ CF-Connecting-IP Check    │
              │ URI Path Caveat Check     │
              └─────────────┬─────────────┘
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
         [Authorized]            [Replay / Stolen]
       Forward to Origin        Deceptive Honey-Route
                                (Synthetic Canaries)
```

## Running Locally

To test this Worker locally using Wrangler (Node.js):

```bash
# In this directory
npx wrangler dev
```

Test valid token generation or execution against local port:
```bash
curl -i http://localhost:8787/api/v1/workloads \
  -H "Authorization: Bearer cap_v1_..."
```
