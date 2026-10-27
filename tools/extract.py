import sys, zipfile, re, os

src, dst = sys.argv[1], sys.argv[2]

def mangle(p):
    return re.sub(r"[A-Z]", lambda m: "_" + m.group(0).lower(), p)

n = 0
with zipfile.ZipFile(src) as z:
    for i in z.infolist():
        if i.is_dir() or not i.filename.startswith("smali/"):
            continue
        out = os.path.join(dst, mangle(i.filename))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with z.open(i) as f, open(out, "wb") as o:
            o.write(f.read())
        n += 1
print(n)
