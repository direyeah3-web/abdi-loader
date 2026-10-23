import re, shutil

p = "app/src/main/java/com/abdi/loader/MainActivity.kt"
shutil.copy(p, p + ".bak")
t = open(p, encoding="utf-8").read()

pat = re.compile(
    r'try\s*\{\s*startActivity\(launch\)\s*\}\s*catch\s*\(e:\s*Exception\)\s*\{\s*'
    r'Toast\.makeText\(this@MainActivity,\s*"Could not open",\s*Toast\.LENGTH_SHORT\)\.show\(\)\s*\}'
)

if not pat.search(t):
    print("❌ Ma helin code-ka Open")
    raise SystemExit

t = pat.sub("GameLauncher.launch(this@MainActivity, pkg)", t, count=1)
open(p, "w", encoding="utf-8").write(t)
print("✅ Open button waa lagu xiray GameLauncher")
