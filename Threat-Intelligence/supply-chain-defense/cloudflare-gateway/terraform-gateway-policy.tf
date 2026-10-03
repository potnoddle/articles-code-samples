# Terraform configuration for Cloudflare Zero Trust Gateway
# Implements destination-side egress filtering for enterprise AI infrastructure

terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

variable "account_id" {
  type        = string
  description = "Cloudflare Account ID"
}

# Rule 1: Block Unapproved Model Registries
resource "cloudflare_teams_rule" "block_unapproved_model_registries" {
  account_id  = var.account_id
  name        = "Block Unapproved Foreign Model Registries"
  description = "Prevents downloading unaligned open-source models onto internal engineering networks"
  precedence  = 1
  action      = "block"
  enabled     = true
  filters     = ["http"]
  traffic     = "http.request.host in {\"modelscope.cn\"} or (http.request.host == \"huggingface.co\" and not http.request.uri matches \"^/enterprise-approved-models/\")"

  rule_settings {
    block_page_enabled = true
    block_reason       = "Open-weight downloads require internal mechanistic security certification."
  }
}

# Rule 2: Force Routing Through Cloudflare AI Gateway
resource "cloudflare_teams_rule" "enforce_ai_gateway" {
  account_id  = var.account_id
  name        = "Enforce Enterprise AI Gateway"
  description = "Redirects outbound LLM inference calls through Cloudflare AI Gateway to enforce anti-distillation monitoring"
  precedence  = 2
  action      = "isolate"
  enabled     = true
  filters     = ["http"]
  traffic     = "http.request.host in {\"api.anthropic.com\", \"api.openai.com\"} and not http.request.headers[\"cf-ai-gateway-authenticated\"] == \"true\""
}
