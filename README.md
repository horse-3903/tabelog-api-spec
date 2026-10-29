<div align="center">

# Tabelog API: Unofficial OpenAPI Spec

Unofficial Tabelog API documentation as an OpenAPI 3.0.3 spec: 62 operations for the Tabelog Inbound mobile app, ready for Swagger UI, Postman or SDK generation.

[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.0.3-6BA539?style=flat-square&logo=openapiinitiative&logoColor=white)](tabelog-openapi.yaml)
[![Python](https://img.shields.io/badge/Python_3.10-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/github/license/horse-3903/tabelog-api-spec?style=flat-square)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/horse-3903/tabelog-api-spec?style=flat-square)](../../commits)

</div>

---

## Overview

**Tabelog API** is a reverse-engineered, unofficial OpenAPI description of the Tabelog Inbound app backend (`com.kakaku.tabelog.tourists` 2.24.1), the English-language Tabelog app for travellers to Japan. It covers restaurant search and detail, areas, saved lists, visited logs, reservations, notifications and account login. Use it to generate a Tabelog API client or SDK in any language with `openapi-generator`.

---

## Features

- **62 operations** - 61 Tabelog endpoints under `/tabelog_inbound_appli/` plus one Google Routes call
- **221 schemas** - request bodies, responses and enums taken from the app's serializers
- **Auth flow documented** - email one-time-password login, anonymous secret token and access token rotation
- **Honest about gaps** - generated from code only, so required fields, nullability and per-endpoint auth are inferred, not verified

---

## Tech Stack

![OpenAPI](https://img.shields.io/badge/OpenAPI-6BA539?style=for-the-badge&logo=openapiinitiative&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![YAML](https://img.shields.io/badge/YAML-CB171E?style=for-the-badge&logo=yaml&logoColor=white)

---

## Getting Started

### Prerequisites

- Python 3.10+
- A decompiled `com.kakaku.tabelog.tourists` 2.24.1 zip (smali)
- `pip install openapi-spec-validator`

### Use the spec

Open `tabelog-openapi.yaml` (or `tabelog-openapi.json`) in Swagger UI, Postman or Insomnia, or generate a client:

```bash
npx @openapitools/openapi-generator-cli generate -i tabelog-openapi.yaml -g python -o tabelog-client
```

### Regenerate

```bash
python tools/extract.py <decompiled.zip> <output_dir>
python tools/openapi_gen.py <output_dir>/smali tabelog-openapi
openapi-spec-validator tabelog-openapi.yaml
```

---

## Project Structure

```
tabelog-api-spec/
├── tabelog-openapi.yaml     # OpenAPI 3.0.3 spec
├── tabelog-openapi.json     # same spec as JSON
├── NOTES.md                 # endpoint notes and auth flow
├── AGENTS.md                # instructions for AI coding agents
└── tools/
    ├── extract.py           # case-safe smali extraction from the zip
    └── openapi_gen.py       # smali to OpenAPI generator
```

---

## Authentication

| Item | Value |
|---|---|
| Base URL | `https://api.tabelog.com` (assembled in code, not confirmed) |
| `X-Tabelog-Secret-Token` | Anonymous device token, requested with a random UUID |
| `X-Tabelog-Access-Token` | Issued after email one-time-password login |
| Token rotation | `GET account/latest` returns a new access token and revokes the previous one |

See [NOTES.md](NOTES.md) for the rest. Unofficial and not affiliated with Tabelog or Kakaku.com.

---

## FAQ

**Is there an official Tabelog API?** Tabelog has no public developer API for restaurant data. This repo documents the private API used by the Tabelog Inbound app, reverse engineered from the app, so it can change without notice.

**Is there a Tabelog SDK?** This repo ships the Tabelog OpenAPI (Swagger) spec, from which you can generate a Tabelog API client or SDK in Python, TypeScript, Go and more with `openapi-generator`.

**What can the Tabelog API do?** Search Japanese restaurants, read restaurant details and areas, manage saved lists and visited logs, make reservations and handle notifications and login.

**Is there a Tabelog MCP server?** Yes: [tabelog-mcp](https://github.com/horse-3903/tabelog-mcp) lets Claude and other AI assistants use this API.

**Which Tabelog version is documented?** Tabelog Inbound (`com.kakaku.tabelog.tourists`) 2.24.1.

---

## Disclaimer

**Use at your own risk.** Calling these APIs outside the official app may violate the service's terms and can lead to rate limiting, a suspended or banned account, or loss of data. The authors accept no responsibility for any consequences to your account. Use only your own account, and never share your credentials or tokens.

---

## Related

- [beli-api-spec](https://github.com/horse-3903/beli-api-spec): the sibling unofficial API spec
- [tabelog-mcp](https://github.com/horse-3903/tabelog-mcp): MCP server built on this spec
