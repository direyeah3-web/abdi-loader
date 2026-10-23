from pathlib import Path
from datetime import datetime

root = Path.home() / "abdi-loader"
p = root / "app/src/main/java/com/abdi/loader/GameLauncher.kt"

if not p.exists():
    raise SystemExit("GameLauncher.kt lama helin")

backup = root / "backups" / (
    "obb-folder-" + datetime.now().strftime("%Y%m%d-%H%M%S")
)
backup.mkdir(parents=True, exist_ok=True)
(backup / p.name).write_text(p.read_text())

s = p.read_text()

# Android-ka ma siin karo app-ka marin u helidda dhammaan meelaha
# kaydka haddii folder la doorto la'aan; isticmaal folder picker.
s = s.replace(
    'import android.app.Activity',
    'import android.app.Activity\n'
    'import android.content.Intent\n'
    'import android.net.Uri\n'
    'import androidx.documentfile.provider.DocumentFile'
)

# Patch-kan si ula kac ah uma beddelayo launcher-ka oo dhan,
# maadaama folder picker-ku u baahan yahay in Activity-gu natiijada
# doorashada gudbiyo. Waxaan kaliya xaqiijinaynaa in la haysto
# meel sax ah oo OBB-ga laga akhriyo ka hor inta aan la sii wadin.
if "DocumentFile" not in s:
    raise SystemExit("DocumentFile import lama gelin")

p.write_text(s)
print("Imports waa la diyaariyey; backup:", backup)
print("Ha push-gareyn weli: folder-picker callback-ka MainActivity waa in lagu xiraa.")
