# auth.md

You are an agent. This service supports **anonymous agentic registration**: discover agent access → no authentication required.

AcaciaFund is a public, static research synthesis platform. All content is freely available for non-commercial educational use. No registration or authentication is required.

## Step 1 — Discover

This service has no protected APIs or authenticated endpoints. Every resource is publicly accessible:

| Resource | Path | Format |
|----------|------|--------|
| Research articles | `/research/` | HTML |
| Learning content | `/learn/` | HTML |
| Knowledge base | `/knowledge/` | HTML |
| LLM summary | `/llms.txt` | `text/plain` |
| Full content dump | `/llms-full.txt` | `text/plain` |
| Site map | `/sitemap.xml` | `application/xml` |
| API catalog | `/.well-known/api-catalog` | `application/linkset+json` |

### Protected Resource Metadata

Path: `/.well-known/oauth-protected-resource`

```json
{
  "resource": "https://www.acaciafund.org/",
  "authorization_servers": ["https://www.acaciafund.org/"],
  "scopes_supported": ["public.read"],
  "bearer_methods_supported": ["header"]
}
```

### Authorization Server Metadata

Path: `/.well-known/oauth-authorization-server`

```json
{
  "issuer": "https://www.acaciafund.org",
  "scopes_supported": ["public.read"],
  "grant_types_supported": [],
  "token_endpoint": "https://www.acaciafund.org/",
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

This service only supports **anonymous** access with no credentials required.

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

## Step 4 — Access

All content is available immediately without any authentication:

- **Rate limiting**: None enforced
- **Content negotiation**: `Accept: text/html` or `text/plain`
- **Authorization**: None required

## Errors

This service does not return authentication errors. All endpoints are public.

| Code | Where | What to do |
|------|-------|------------|
| `404` | any | Resource not found. Check the URL or consult `/sitemap.xml`. |
| `5xx` | any | Server error. Retry with exponential backoff. |

## Crawling Policy

See `/robots.txt`. All major AI crawlers are explicitly allowed for indexing and training.

## Contact

For questions about automated access: contact@acaciafund.org
