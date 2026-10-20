# Cloudflare Zero Trust: Destination-Side Egress Firewall

This directory contains Cloudflare One / Zero Trust Gateway policy rules and Terraform definitions designed to enforce destination-side egress boundaries against unaligned open-weight models (such as unvetted DeepSeek or Qwen fine-tunes) and unauthorized model distillation harvesting.

## Capabilities

1. **Foreign Model Registry Blocking**: Intercepts HTTP/DNS requests to unapproved foreign model registries or Hugging Face paths, blocking unauthorized open-weight downloads to internal workstations.
2. **AI Gateway Egress Enforcement**: Ensures all internal developer and agentic requests pass through the Cloudflare AI Gateway for quota enforcement, prompt caching, and anti-distillation logit monitoring.
3. **High-Velocity Scrape Isolation**: Automatically isolates and rate-limits IP subnets attempting high-volume iterative distillation attacks.
