import shutil
p = "app/src/main/java/com/abdi/loader/GameLauncher.kt"
shutil.copy(p, p + ".bak_diag")
s = open(p).read()
old = 'Toast.makeText(activity, "Loader error: ${e.message}", Toast.LENGTH_LONG).show()'
new = '''val trace = Log.getStackTraceString(e).lines().take(18).joinToString("\\n")
                    android.app.AlertDialog.Builder(activity)
                        .setTitle("Loader error")
                        .setMessage(trace)
                        .setPositiveButton("OK", null)
                        .show()'''
if old not in s:
    print("Sadarkii la raadinayay lama helin, wax la beddelay ma jiro")
else:
    open(p, "w").write(s.replace(old, new, 1))
    print("OK")
