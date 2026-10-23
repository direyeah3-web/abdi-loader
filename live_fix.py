import re, shutil

p = "app/src/main/java/com/abdi/loader/MainActivity.kt"
shutil.copy(p, p + ".bak2")
t = open(p, encoding="utf-8").read()

def once(pat, rep, flags=0, name=""):
    global t
    n = len(re.findall(pat, t, flags))
    if n != 1:
        print(f"❌ {name}: la helay {n} meel (waa inuu noqdaa 1)")
        raise SystemExit
    t = re.sub(pat, rep, t, count=1, flags=flags)

# 1. Key-ga qoran oo la keydiyo (draft)
watcher = (
    'hint = "Enter license key"\n'
    '                addTextChangedListener(object : android.text.TextWatcher {\n'
    '                    override fun afterTextChanged(s: android.text.Editable?) {\n'
    '                        prefs().edit().putString("draft", s?.toString() ?: "").apply()\n'
    '                    }\n'
    '                    override fun beforeTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}\n'
    '                    override fun onTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}\n'
    '                })'
)
once(r'hint = "Enter license key"', lambda m: watcher, name="hint")

once(r'verify\(saved\) \} else showLogin\(""\, ""\)',
     lambda m: 'verify(saved) } else showLogin("", prefs().getString("draft", "") ?: "")',
     name="onCreate")

once(r'prefs\(\)\.edit\(\)\.putString\("key", key\)\.apply\(\)',
     lambda m: 'prefs().edit().putString("key", key).remove("draft").apply()',
     name="verify save")

once(r'prefs\(\)\.edit\(\)\.remove\("key"\)\.apply\(\)',
     lambda m: 'prefs().edit().remove("key").remove("draft").apply()',
     name="logout")

# 2. Tirin socota
once(r'^(\s*)text = big\s*$',
     lambda m: m.group(1) + 'text = big\n' + m.group(1) + 'bigView = this',
     flags=re.M, name="text = big")

once(r'val dot = View\(this\)\.apply \{',
     lambda m: 'val dot = View(this).apply {\n            dotView = this',
     name="dot")

once(r'^(\s*)dotColor = if \(days <= 3L\) RED else if \(days <= 7L\) ORANGE else GREEN\s*$',
     lambda m: m.group(0).rstrip("\n") + '\n' + m.group(1) + 'startTicker(ms)',
     flags=re.M, name="dotColor")

funcs = '''    private var bigView: TextView? = null
    private var dotView: View? = null
    private var tickGen = 0
    private val tickHandler = android.os.Handler(android.os.Looper.getMainLooper())

    private fun fmtLeft(left: Long): String {
        if (left <= 0L) return "Expired"
        val s = left / 1000
        val d = s / 86400
        val h = (s % 86400) / 3600
        val m = (s % 3600) / 60
        val sec = s % 60
        return if (d > 0) "${d}d ${h}h ${m}m ${sec}s" else "${h}h ${m}m ${sec}s"
    }

    private fun startTicker(ms: Long) {
        val gen = ++tickGen
        val r = object : Runnable {
            override fun run() {
                val bv = bigView
                if (gen != tickGen || bv == null || !bv.isAttachedToWindow) return
                val left = ms - System.currentTimeMillis()
                bv.textSize = 30f
                bv.maxLines = 1
                bv.text = fmtLeft(left)
                val days = Math.ceil(left / 86400000.0).toLong()
                val c = if (days <= 3L) RED else if (days <= 7L) ORANGE else GREEN
                (dotView?.background as? GradientDrawable)?.setColor(c)
                if (left > 0) tickHandler.postDelayed(this, 1000)
            }
        }
        tickHandler.postDelayed(r, 500)
    }

'''
once(r'    private fun parseMs\(', lambda m: funcs + '    private fun parseMs(', name="parseMs")

open(p, "w", encoding="utf-8").write(t)
print("✅ Waa la xaliyay: key draft + tirin socota")
