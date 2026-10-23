from pathlib import Path
from zipfile import ZipFile

roots = [
    Path.home(),
    Path("/storage/emulated/0"),
]

found = []

for root in roots:
    if not root.exists():
        continue
    try:
        for p in root.rglob("Bcore-release.aar"):
            found.append(p)
            if len(found) >= 10:
                break
    except (PermissionError, OSError):
        pass
    if found:
        break

if not found:
    print("Bcore-release.aar lama helin.")
    print("Hubi inuu Termux heli karo storage-ka telefoonka.")
    raise SystemExit

for aar in found:
    print(f"\nAAR: {aar}")
    try:
        with ZipFile(aar) as z:
            names = z.namelist()
            for name in names:
                print(" -", name)

            if "AndroidManifest.xml" in names:
                print("\nManifest-ka binary ayuu noqon karaa.")

            if "classes.jar" in names:
                import io
                with ZipFile(io.BytesIO(z.read("classes.jar"))) as jar:
                    print("\nClasses la xiriiri kara virtual space:")
                    matches = [
                        n for n in jar.namelist()
                        if n.endswith(".class")
                        and any(word in n.lower() for word in (
                            "virtual", "core", "plugin", "sandbox",
                            "blackbox", "activitymanager"
                        ))
                    ]
                    print("\n".join(matches[:100]) or "Wax u dhigma lama helin.")
    except Exception as e:
        print("Akhrinta AAR way fashilantay:", e)
