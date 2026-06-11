# auth.md

You are an agent. This service supports **anonymous agentic registration**: discover → register → access content. No authentication required.

## Step 1 — Discover

This service has no protected APIs. All content is publicly accessible.

### 1a. Fetch Protected Resource Metadata

```http
GET /.well-known/oauth-protected-resource
```

```json
{
  "resource": "https://www.acaciafund.org/",
  "authorization_servers": ["https://www.acaciafund.org"],
  "scopes_supported": ["public.read"],
  "bearer_methods_supported": ["header"]
}
```

### 1b. Fetch Authorization Server Metadata

```http
GET /.well-known/oauth-authorization-server
```

```json
{
  "issuer": "https://www.acaciafund.org",
  "agent_auth": {
    "skill": "https://www.acaciafund.org/auth.md",
    "identity_types_supported": ["anonymous"],
    "anonymous": {
      "credential_types_supported": ["none"]
    },
    "claim_uri": "https://www.acaciafund.org/auth.md#claim"
  }
}
```

## Step 2 — Pick a method

This service supports only **anonymous** access — no identity assertion, no email, no credentials.

**identity_types_supported**: `["anonymous"]`

## Step 3 — Register

No registration required. Send direct HTTP GET requests to any public URL.

### anonymous

```http
GET /research/aml-risk-assessment
Accept: text/html
```

Response (200):

```html
<html>...full research article...</html>
```

**identity_types_supported**: `["anonymous"]`
**credential_type**: `none`

## Step 4 — Claim ceremony

No claim ceremony needed. Anonymous access grants full read access immediately.

### claim_uri

`https://www.acaciafund.org/auth.md#claim`

## Step 5 — Access content

All resources are freely available:

| Path | Content | Format |
|------|---------|--------|
| `/research/` | Research articles | HTML |
| `/learn/` | Learning content | HTML |
| `/knowledge/` | Quick references | HTML |
| `/llms.txt` | Agent overview | `text/plain` |
| `/llms-full.txt` | Full content dump | `text/plain` |
| `/.well-known/api-catalog` | API catalog | `application/linkset+json` |

## Errors

| Code | Meaning |
|------|---------|
| `404` | Resource not found |
| `5xx` | Server error — retry |

## Crawling

See `/robots.txt`. All major AI crawlers are explicitly allowed. Contact: contact@acaciafund.org
