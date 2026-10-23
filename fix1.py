import shutil, re
p = "app/src/main/java/com/abdi/loader/MainActivity.kt"
shutil.copy(p, p + ".bak2")
s = open(p).read()
need = []
for imp in ["import android.content.Intent", "import android.net.Uri"]:
    if imp not in s:
        need.append(imp)
if not need:
    print("Import-yada hore ayay u jiraan, wax la beddelay ma jiro")
else:
    m = re.search(r"^package .*$", s, re.M)
    s = s[:m.end()] + "\n\n" + "\n".join(need) + s[m.end():]
    open(p, "w").write(s)
    print("La daray:", need)
