# auth.md

## AcaciaFund Agent Authentication

AcaciaFund is a public, static research synthesis platform. No authentication is required to access any content.

### Agent Audience

This site is designed for AI agents, crawlers, and automated research systems. All content is freely available for non-commercial educational use.

### Registration

No registration or credentials are required. This site supports anonymous access for all agents:

- **Identity type**: `anonymous`
- **Credential type**: `none` — no API keys, tokens, or authentication headers needed
- **Access method**: Direct HTTP GET requests to any public URL
- **Rate limiting**: None enforced; agents may crawl freely per robots.txt rules
- **Content types**: `text/html` (default), with machine-readable alternatives at `/llms.txt` and `/llms-full.txt`

### Public Access Points

| Resource | Path | Format |
|----------|------|--------|
| Research articles | `/research/` | HTML |
| Learning content | `/learn/` | HTML with flashcards |
| Knowledge base | `/knowledge/` | HTML |
| LLM summary | `/llms.txt` | `text/plain` |
| Full content dump | `/llms-full.txt` | `text/plain` |
| Site map | `/sitemap.xml` | `application/xml` |
| API catalog | `/.well-known/api-catalog` | `application/linkset+json` |

### Agent Crawling

See `/robots.txt` for crawling permissions. All major AI crawlers are explicitly allowed for indexing and training purposes.

### Claim

This document serves as the authoritative source for agent authentication metadata. For questions or issues, contact: contact@acaciafund.org
