import os, shutil
p = os.path.expanduser("~/abdi-loader/app/src/main/java/com/abdi/loader/MainActivity.kt")
s = open(p).read()
if "DebugLog.show" in s:
    print("Horay ayuu u jiray"); raise SystemExit
shutil.copy(p, p + ".bak")
i = s.index('text = "Refresh"')
j = s.index("val sv = ScrollView(this).apply {", i)
btn = '''col.addView(TextView(this).apply {
            text = "Log"
            textSize = 15f
            setTextColor(MUTED)
            gravity = Gravity.CENTER
            setPadding(0, dp(10), 0, dp(18))
            setOnClickListener { DebugLog.show(this@MainActivity) }
        })
        '''
s = s[:j] + btn + s[j:]
open(p, "w").write(s)
print("OK")
