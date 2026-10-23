from pathlib import Path
import re
from datetime import datetime

root = Path.home() / "abdi-loader"
manifest = root / "app/src/main/AndroidManifest.xml"
application = root / "app/src/main/java/com/abdi/loader/AbdiApplication.kt"
launcher = root / "app/src/main/java/com/abdi/loader/GameLauncher.kt"

for p in (manifest, application, launcher):
    if not p.exists():
        raise SystemExit(f"JOOJI: file lama helin: {p}")

backup = root / "backups" / ("init-fix-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
backup.mkdir(parents=True)
for p in (manifest, application, launcher):
    (backup / p.name).write_text(p.read_text())

# Ensure Android actually loads AbdiApplication.
s = manifest.read_text()
m = re.search(r"<application\b[^>]*>", s, re.S)
if not m:
    raise SystemExit("JOOJI: <application> lama helin AndroidManifest.xml")

tag = m.group(0)
if re.search(r'\bandroid:name\s*=', tag):
    tag = re.sub(
        r'\bandroid:name\s*=\s*["\'][^"\']*["\']',
        'android:name=".AbdiApplication"',
        tag,
        count=1
    )
else:
    tag = tag[:-1] + ' android:name=".AbdiApplication">'
s = s[:m.start()] + tag + s[m.end():]
manifest.write_text(s)

# Keep the engine startup in Application and make startup errors visible in logs.
application.write_text("""package com.abdi.loader

import android.app.Application
import android.content.Context
import android.util.Log
import top.niunaijun.blackbox.BlackBoxCore
import top.niunaijun.blackbox.app.configuration.ClientConfiguration

class AbdiApplication : Application() {
    override fun attachBaseContext(base: Context) {
        super.attachBaseContext(base)
        BlackBoxCore.get().doAttachBaseContext(
            base,
            object : ClientConfiguration() {
                override fun getHostPackageName(): String = base.packageName
            }
        )
        Log.i("AbdiLoader", "BlackBoxCore attached: ${base.packageName}")
    }

    override fun onCreate() {
        super.onCreate()
        BlackBoxCore.get().doCreate()
        Log.i("AbdiLoader", "BlackBoxCore created")
    }
}
""")

# Log the full exception instead of showing only a truncated message.
g = launcher.read_text()
if "Log.e(\"AbdiLoader\"" not in g:
    g = g.replace(
        'import android.widget.Toast',
        'import android.widget.Toast\nimport android.util.Log'
    )
    g = g.replace(
        'Toast.makeText(activity,"Virtual engine error: ${e.message}",Toast.LENGTH_SHORT).show()',
        'Log.e("AbdiLoader", "Virtual engine failed for $pkg", e)\n'
        'Toast.makeText(activity, "Virtual engine error: ${e.javaClass.simpleName}: ${e.message}", Toast.LENGTH_LONG).show()'
    )
    launcher.write_text(g)

print("OK: Application manifest iyo initialization waa la saxay.")
print("Backup:", backup)
print("Manifest app name:", re.search(
    r'<application\b[^>]*\bandroid:name=["\']([^"\']+)',
    manifest.read_text(), re.S
).group(1))
print("Hubi isbeddellada, kadib git push samee.")
