import json
import re
import sys
from pathlib import Path

SMALI = Path(sys.argv[1])
OUT = Path(sys.argv[2])

VERB = {"b": "delete", "f": "get", "g": "head", "n": "patch", "o": "post", "p": "put"}
PARAM = {"a": "Body", "c": "Field", "d": "FieldMap", "i": "Header", "j": "HeaderMap", "q": "Part", "s": "Path", "t": "Query", "u": "QueryMap", "y": "Url"}
MODE = {"e": "form", "l": "multipart"}
PRIM = {"I": {"type": "integer"}, "J": {"type": "integer", "format": "int64"}, "S": {"type": "integer"}, "B": {"type": "integer"},
        "Z": {"type": "boolean"}, "F": {"type": "number", "format": "float"}, "D": {"type": "number", "format": "double"}}
BOXED = {"java/lang/Integer": PRIM["I"], "java/lang/Long": PRIM["J"], "java/lang/Boolean": PRIM["Z"], "java/lang/Double": PRIM["D"],
         "java/lang/Float": PRIM["F"], "java/lang/String": {"type": "string"}, "android/net/Uri": {"type": "string", "format": "uri"},
         "java/time/LocalDate": {"type": "string", "format": "date"}, "java/time/LocalDateTime": {"type": "string", "format": "date-time"},
         "java/time/LocalTime": {"type": "string"}, "java/lang/Object": {}, "kotlin/Unit": {}}

components = {}
building = set()


def mangle(p):
    return re.sub(r"[A-Z]", lambda m: "_" + m.group(0).lower(), p)


def parse_type(s, i=0):
    c = s[i]
    if c in PRIM:
        return {"k": "prim", "v": c}, i + 1
    if c == "[":
        t, j = parse_type(s, i + 1)
        return {"k": "arr", "t": t}, j
    if c == "T":
        j = s.index(";", i)
        return {"k": "any"}, j + 1
    if c == "*":
        return {"k": "any"}, i + 1
    if c in "+-":
        return parse_type(s, i + 1)
    assert c == "L", (s, i)
    j = i + 1
    while s[j] not in "<;":
        j += 1
    name, args = s[i + 1:j], []
    if s[j] == "<":
        j += 1
        while s[j] != ">":
            t, j = parse_type(s, j)
            args.append(t)
        j += 1
    while s[j] == ".":
        k = j + 1
        while s[k] not in "<;":
            k += 1
        name += "$" + s[j + 1:k]
        j = k
        if s[j] == "<":
            j += 1
            while s[j] != ">":
                _, j = parse_type(s, j)
            j += 1
    assert s[j] == ";", (s, j)
    return {"k": "cls", "n": name, "a": args}, j + 1


def parse_sig(s):
    assert s[0] == "("
    i, params = 1, []
    while s[i] != ")":
        t, i = parse_type(s, i)
        params.append(t)
    ret, _ = parse_type(s, i + 1) if s[i + 1] != "V" else ({"k": "void"}, 0)
    return params, ret


def sig_strings(block):
    m = re.search(r"Ldalvik/annotation/Signature;\s*value = \{(.*?)\}\s*\.end annotation", block, re.S)
    return "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))) if m else None


def snake(n):
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", n).lower()


def section(f, cls):
    text = f.read_text(encoding="utf-8", errors="ignore")
    marks = [(m.start(), m.group(1)) for m in re.finditer(r"^\.class [^\n]*? L([^;]+);", text, re.M)]
    for i, (pos, nm) in enumerate(marks):
        if nm == cls:
            return text[pos:marks[i + 1][0] if i + 1 < len(marks) else len(text)]
    return None


def comp_name(cls):
    return cls.split("/")[-1].replace("$", "_")


def schema(t):
    k = t["k"]
    if k == "prim":
        return dict(PRIM[t["v"]])
    if k == "arr":
        return {"type": "array", "items": schema(t["t"])}
    if k == "any":
        return {}
    if k == "void":
        return {}
    n = t["n"]
    if n in BOXED:
        return dict(BOXED[n])
    if n in ("java/util/List", "java/util/Collection", "java/util/Set"):
        return {"type": "array", "items": schema(t["a"][0]) if t["a"] else {}}
    if n == "java/util/Map":
        return {"type": "object", "additionalProperties": schema(t["a"][1]) if len(t["a"]) > 1 else {}}
    if n.startswith("com/kakaku/"):
        return {"$ref": "#/components/schemas/" + build(n)}
    return {}


def build(cls):
    name = comp_name(cls)
    if name in components or name in building:
        return name
    f = SMALI / (mangle(cls.split("$")[0]) + ".smali")
    text = section(f, cls) if f.exists() else None
    if text is None:
        components[name] = {"type": "object", "description": "class not found in decompilation: " + cls}
        return name
    building.add(name)
    if re.search(r"^\.super Ljava/lang/Enum;", text, re.M):
        vals = re.findall(r"^\.field [^\n]*\benum (\w+):", text, re.M)
        out_vals = []
        for v in vals:
            pm = re.search(r'const-string v\d+, "([^"]*)"\s*\n\s*const-string v\d+, "' + re.escape(v) + '"', text)
            out_vals.append(pm.group(1) if pm and pm.group(1) not in vals else v)
        components[name] = {"type": "string", "enum": out_vals, "x-class": cls}
    else:
        props = {}
        for m in re.finditer(r"^\.field ([^\n]*)\n((?:[ \t][^\n]*\n|\n)*)", text, re.M):
            head, chunk = m.group(1), m.group(2)
            mm = re.match(r"(.*?)(\w+):(\S+?)(?:\s*=.*)?$", head)
            if not mm:
                continue
            mods, fname, desc = mm.group(1).split(), mm.group(2), mm.group(3)
            if "static" in mods or "synthetic" in mods or fname.startswith("$"):
                continue
            sig = sig_strings(chunk) or desc
            try:
                t, _ = parse_type(sig)
            except Exception:
                continue
            props[snake(fname)] = schema(t)
        components[name] = {"type": "object", "properties": props, "x-class": cls}
    building.discard(name)
    return name


def op_id(path):
    parts = re.split(r"[/_:]+", path.replace("/tabelog_inbound_appli", "").strip("/"))
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def tag_of(path):
    p = path.replace("/tabelog_inbound_appli/", "")
    for pre, tag in (("account", "Account"), ("onetime_password", "Account"), ("secret_token", "Account"), ("push_device_token", "Account"),
                     ("hozon_", "Saved lists"), ("visited_", "Visited"), ("reservation", "Reservations"), ("area_", "Areas"),
                     ("notification", "Notifications"), ("information", "Notifications"), ("check_japan", "Utilities")):
        if p.startswith(pre):
            return tag
    return "Restaurants"


def needs_login(path):
    p = path.replace("/tabelog_inbound_appli/", "")
    if p in ("account/authenticate", "account/token", "account/register", "onetime_password/send", "secret_token_generate/create"):
        return False
    return p.startswith(("account/", "hozon_", "visited_", "notification", "reservation/", "push_device_token"))


ann_re = re.compile(r"\.annotation runtime L([\w/$]+);\n(?:\s+value = ([^\n]*)\n)?\s*\.end annotation")
meth_re = re.compile(r"\.method public abstract (\w+)\(([^)]*)\)(\S+)\n(.*?)\n\.end method", re.S)

paths = {}
tags_seen = []
for d, servers in (("_m9", None), ("_n9", "https://routes.googleapis.com")):
    for f in sorted((SMALI / d).glob("*.smali")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        cls = re.search(r"^\.class [^\n]*? L([^;]+);", text, re.M).group(1)
        for m in meth_re.finditer(text):
            mname, desc, ret, body = m.groups()
            pblocks = list(re.finditer(r"\.param (p\d+)\s+# (\S+)\n(.*?)\.end param", body, re.S))
            stripped = re.sub(r"\.param .*?\.end param", "", body, flags=re.S)
            verb = path = None
            mode = None
            for a in ann_re.finditer(stripped):
                if not a.group(1).startswith("Cb/"):
                    continue
                k = a.group(1)[3:]
                if k in VERB:
                    verb, path = VERB[k], (a.group(2) or '""').strip('"')
                elif k in MODE:
                    mode = MODE[k]
            if not verb:
                continue
            sig = sig_strings(stripped) or "(" + desc + ")" + ret
            ptypes, _ = parse_sig(sig)
            m2 = re.search(r"Lta/a<-?(.*)>;\)", sig)
            res_t = None
            if m2:
                res_t, _ = parse_type(m2.group(1))
            ptypes = ptypes[:-1]
            params, form, body_schema = [], {}, None
            for idx, pb in enumerate(pblocks):
                t = ptypes[idx]
                for a in ann_re.finditer(pb.group(3)):
                    if not a.group(1).startswith("Cb/") or a.group(1)[3:] not in PARAM:
                        continue
                    kind = PARAM[a.group(1)[3:]]
                    nm = (a.group(2) or "").strip('"')
                    sc = schema(t)
                    if nm == "lang":
                        sc = {"type": "string", "enum": ["en", "tw", "kr", "th"], "default": "en"}
                    if kind == "Query":
                        params.append({"name": nm, "in": "query", "schema": sc, **({"style": "form", "explode": True} if nm.endswith("[]") else {})})
                    elif kind == "Header":
                        params.append({"name": nm, "in": "header", "required": True, "schema": sc})
                    elif kind == "Path":
                        params.append({"name": nm, "in": "path", "required": True, "schema": sc})
                    elif kind == "Field":
                        form[nm] = sc
                    elif kind == "Body":
                        body_schema = sc
            full = (servers or "") + ("/" + path.lstrip("/") if servers else path)
            op = {"operationId": op_id(full) if not servers else "computeRoutes", "tags": ["Google Routes"] if servers else [tag_of(path)],
                  "x-android-method": cls.replace("/", ".") + "." + mname}
            if params:
                op["parameters"] = params
            if body_schema is not None:
                op["requestBody"] = {"required": True, "content": {"application/json": {"schema": body_schema}}}
            elif form:
                op["requestBody"] = {"required": True, "content": {"application/x-www-form-urlencoded": {"schema": {"type": "object", "properties": form}}}}
            rs = schema(res_t) if res_t else {}
            resp = {"description": "OK"}
            if rs and not (res_t["k"] == "cls" and res_t["n"] == "kotlin/Unit"):
                resp["content"] = {"application/json": {"schema": rs}}
            op["responses"] = {"200": resp}
            if not servers:
                op["responses"]["default"] = {"description": "Error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ApiError"}}}}
                op["security"] = [{"SecretToken": [], "AccessToken": []}] if needs_login(path) else [{"SecretToken": []}]
                op["parameters"] = [{"$ref": "#/components/parameters/AppVersion"}] + op.get("parameters", [])
            else:
                op["security"] = []
            key = path if not servers else path
            entry = paths.setdefault(key if not servers else "/" + path.lstrip("/"), {})
            if servers:
                entry["servers"] = [{"url": servers}]
            entry[verb] = op
            if op["tags"][0] not in tags_seen:
                tags_seen.append(op["tags"][0])

components["ApiError"] = {"type": "object", "properties": {"error": {"type": "object", "properties": {
    "status": {"type": "integer"}, "type": {"type": "string", "example": "unavailableAccessToken"},
    "internal_report_message": {"type": "string"}, "message": {"type": "string"}}}}}

desc = """Reverse-engineered from the decompiled Android app `com.kakaku.tabelog.tourists` 2.24.1 (Tabelog Inbound / "TabelogInbound Android").
Unofficial and unverified against the live service apart from the calls noted below. Not endorsed by Kakaku.com.

Observed behaviour:
- Every JSON object in responses also carries `granularity` ("S" seen).
- `GET account/latest` returns a fresh `access_token` and the previous one is then revoked (401 `unavailableAccessToken`, "Token has been revoked"). Clients must store the newest token.
- Auth: an anonymous device-level `X-Tabelog-Secret-Token` is requested via `POST secret_token_generate/create` with a random UUID as `code`; after email one-time-password login, `X-Tabelog-Access-Token` is added. Which endpoints require login is inferred (`security`).
- Property names are snake_case versions of the Kotlin property names (kotlinx.serialization naming strategy), checked against live responses for the account and saved-list objects only.
- List endpoints that accept arrays use `name[]` query or form keys.
- Required/optional and nullability are not recoverable from the bytecode, so nothing is marked required."""

spec = {
    "openapi": "3.0.3",
    "info": {"title": "Tabelog Inbound mobile API (unofficial)", "version": "2.24.1", "description": desc},
    "servers": [{"url": "https://api.tabelog.com", "description": "Assembled in code as 'https://api.' + 'tabelog.com'; not confirmed by a live request to the root"}],
    "tags": [{"name": t} for t in tags_seen],
    "paths": dict(sorted(paths.items())),
    "components": {
        "securitySchemes": {
            "SecretToken": {"type": "apiKey", "in": "header", "name": "X-Tabelog-Secret-Token"},
            "AccessToken": {"type": "apiKey", "in": "header", "name": "X-Tabelog-Access-Token"},
        },
        "parameters": {"AppVersion": {"name": "X-Tabelog-Appli-Version", "in": "header", "required": True,
                                      "schema": {"type": "string", "default": "TabelogInbound Android/ver2.24.1"},
                                      "description": "The app also sends the same value as User-Agent."}},
        "schemas": dict(sorted(components.items())),
    },
    "security": [{"SecretToken": []}],
}


def refs(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "$ref":
                yield v
            else:
                yield from refs(v)
    elif isinstance(o, list):
        for v in o:
            yield from refs(v)


missing = [r for r in set(refs(spec)) if r.startswith("#/components/schemas/") and r.split("/")[-1] not in components]
OUT.with_suffix(".json").write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

_plain = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def y(o, ind=0):
    pad = "  " * ind
    out = []
    if isinstance(o, dict):
        if not o:
            return "{}"
        for k, v in o.items():
            ks = k if _plain.match(k) and k.lower() not in ("true", "false", "null", "yes", "no", "on", "off") else json.dumps(k, ensure_ascii=False)
            if isinstance(v, (dict, list)) and v:
                out.append(f"{pad}{ks}:\n{y(v, ind + 1)}")
            else:
                out.append(f"{pad}{ks}: {y(v, ind + 1)}")
        return "\n".join(out)
    if isinstance(o, list):
        if not o:
            return "[]"
        for v in o:
            if isinstance(v, (dict, list)) and v:
                s = y(v, ind + 1).split("\n")
                out.append(f"{pad}- {s[0].lstrip()}\n" + "\n".join(s[1:]) if len(s) > 1 else f"{pad}- {s[0].lstrip()}")
            else:
                out.append(f"{pad}- {y(v, ind + 1)}")
        return "\n".join(out)
    if o is None:
        return "null"
    if isinstance(o, bool):
        return "true" if o else "false"
    if isinstance(o, (int, float)):
        return str(o)
    return json.dumps(o, ensure_ascii=False)


OUT.with_suffix(".yaml").write_text(y(spec) + "\n", encoding="utf-8")
nops = sum(1 for p in paths.values() for k in p if k != "servers")
print("paths", len(paths), "operations", nops, "schemas", len(components), "missing refs", missing)
