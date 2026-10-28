# AGENTS.md: tabelog

OpenAPI 3.0.3 spec for the Tabelog Inbound app backend (`com.kakaku.tabelog.tourists` 2.24.1), reverse engineered from decompiled smali. Nothing was tested against the live service.

## Layout

- `tabelog-openapi.yaml` and `tabelog-openapi.json`: the spec, identical content. Generated, do not hand edit.
- `NOTES.md`: human notes on endpoints, auth flow and quirks.
- `tools/extract.py`: extracts smali from a decompiler zip using case-safe filenames (each uppercase letter becomes `_` plus the lowercase letter, because Windows filesystems collide on `M9/` and `m9/`).
- `tools/openapi_gen.py`: reads the extracted smali and writes the spec. Usage: `python tools/openapi_gen.py <smali_dir> <output_prefix>`.

## Rebuild

```bash
python tabelog/tools/extract.py <decompiled.zip> <output_dir>
python tabelog/tools/openapi_gen.py <output_dir>/smali tabelog/tabelog-openapi
openapi-spec-validator tabelog/tabelog-openapi.yaml
```

## Conventions

- Base URL `https://api.tabelog.com` is assembled in code and unconfirmed.
- `X-Tabelog-Secret-Token` is an anonymous device token; `X-Tabelog-Access-Token` comes from email one-time-password login. Which endpoints need login is inferred.
- `GET account/latest` returns a new `access_token` and revokes the previous one.
- JSON property names are the snake_case form of the Kotlin property names. Enum values come from the serializer names.

## Rules

- Never commit tokens, `.env` files, saved login state, APKs or zips. The root `.gitignore` covers these.
- Specs come from code, not live traffic. Do not mark fields required or nullable unless verified, and say clearly what is verified versus inferred.
- After changing a spec, validate it with `openapi-spec-validator`. Keep YAML and JSON in sync by regenerating both from the script, never by editing one by hand.
- Do not use em dashes in any text. Keep commit messages to one short line, with no Co-Authored-By trailers. Only commit when asked.
