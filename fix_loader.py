from pathlib import Path

root = Path.home() / "abdi-loader"

# Backup the files before editing
for name in ["build.gradle.kts", "settings.gradle.kts"]:
    p = root / name
    (root / "backups").mkdir(exist_ok=True)
    (root / "backups" / (name + ".before-fix")).write_text(
        p.read_text()
    )

# Supply the SDK values required by Bcore/build.gradle
p = root / "build.gradle.kts"
s = p.read_text()
if "compileSdkVersion" not in s:
    s = (
        'extra["compileSdkVersion"] = 36\n'
        'extra["minSdk"] = 24\n\n'
        + s
    )
p.write_text(s)

# Add JitPack for BlackBox dependencies
p = root / "settings.gradle.kts"
s = p.read_text()
if "https://jitpack.io" not in s:
    s = s.replace(
        "repositories { google(); mavenCentral() }",
        "repositories { google(); mavenCentral(); "
        'maven("https://jitpack.io") }'
    )
p.write_text(s)

print("Fixes applied. Backup saved in backups/.")
print("Next: commit and push, then check GitHub Actions.")
