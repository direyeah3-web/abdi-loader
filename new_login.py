import os, re

try:
    from PIL import Image
except ImportError:
    print("❌ Marka hore: pkg install -y python-pillow")
    raise SystemExit

home = os.path.expanduser("~")
cands = [home + "/storage/downloads/zapya/xero.png",
         "/sdcard/Download/zapya/xero.png",
         "/storage/emulated/0/Download/zapya/xero.png"]
src = next((p for p in cands if os.path.exists(p)), None)
if not src:
    print("❌ xero.png lama helin. Orod: termux-setup-storage")
    raise SystemExit

im = Image.open(src).convert("RGBA")
w, h = im.size
s = min(w, h)
im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))

def save(path, size):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.resize((size, size), Image.LANCZOS).save(path, optimize=True)

for d, sz in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
    save("app/src/main/res/mipmap-%s/ic_launcher.png" % d, sz)
save("app/src/main/res/drawable-nodpi/logo.png", 512)
print("✅ Icon + logo waa la sameeyay")

mp = "app/src/main/AndroidManifest.xml"
with open(mp, "r", encoding="utf-8") as f:
    m = f.read()
if "android:icon" not in m:
    m = m.replace('android:label="Abdi Loader"', 'android:label="Abdi Loader"\n        android:icon="@mipmap/ic_launcher"', 1)
    with open(mp, "w", encoding="utf-8") as f:
        f.write(m)
    print("✅ Manifest icon")

kp = "app/src/main/java/com/abdi/loader/MainActivity.kt"
with open(kp, "r", encoding="utf-8") as f:
    k = f.read()
if "class OrbitView" in k:
    print("⚠️ Login cusub hore ayuu u jiray. Waan joogsaday.")
    raise SystemExit

NEW_LOGIN = r'''    private fun showLogin(msg: String, prefill: String) {
        val bgc = Color.parseColor("#050505")
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setBackgroundColor(bgc)
            setPadding(dp(24), dp(36), dp(24), dp(24))
        }
        val stage = FrameLayout(this)
        stage.addView(OrbitView(this), FrameLayout.LayoutParams(MATCH, MATCH))
        val glow = View(this).apply {
            background = GradientDrawable().apply {
                shape = GradientDrawable.OVAL
                gradientType = GradientDrawable.RADIAL_GRADIENT
                gradientRadius = dp(80).toFloat()
                colors = intArrayOf(Color.parseColor("#550A84FF"), Color.TRANSPARENT)
            }
        }
        stage.addView(glow, FrameLayout.LayoutParams(dp(170), dp(170), Gravity.CENTER))
        val logo = ImageView(this).apply {
            setImageResource(R.drawable.logo)
            scaleType = ImageView.ScaleType.CENTER_CROP
        }
        round(logo, 26)
        stage.addView(logo, FrameLayout.LayoutParams(dp(96), dp(96), Gravity.CENTER))
        for (prop in arrayOf("scaleX", "scaleY")) {
            android.animation.ObjectAnimator.ofFloat(logo, prop, 1f, 1.07f).apply {
                duration = 1800
                repeatCount = ValueAnimator.INFINITE
                repeatMode = ValueAnimator.REVERSE
                start()
            }
        }
        root.addView(stage, lp(MATCH, dp(330)))

        root.addView(TextView(this).apply {
            text = "Welcome to\nAbdi Loader"
            textSize = 28f
            setTextColor(Color.WHITE)
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
        })
        root.addView(TextView(this).apply {
            text = "Enter your license key to unlock your games."
            textSize = 14f
            setTextColor(MUTED)
            gravity = Gravity.CENTER
            setPadding(dp(8), dp(10), dp(8), dp(26))
        })

        val pill = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            background = bg(Color.parseColor("#101010"), 28, Color.parseColor("#2A2A2A"))
            setPadding(dp(18), 0, dp(6), 0)
        }
        pill.addView(TextView(this).apply { text = "\uD83D\uDD11"; textSize = 17f })
        val input = EditText(this).apply {
            hint = "Enter license key"
            setHintTextColor(Color.parseColor("#5A5A5E"))
            setTextColor(Color.WHITE)
            textSize = 16f
            typeface = Typeface.MONOSPACE
            background = null
            setPadding(dp(12), 0, dp(8), 0)
            setSingleLine(true)
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
            setText(prefill)
        }
        pill.addView(input, LinearLayout.LayoutParams(0, dp(54), 1f))
        pill.addView(TextView(this).apply {
            text = "Paste"
            textSize = 14f
            setTextColor(BLUE)
            setPadding(dp(10), dp(12), dp(14), dp(12))
            setOnClickListener {
                val cm = this@MainActivity.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val t = cm.primaryClip?.getItemAt(0)?.coerceToText(this@MainActivity)?.toString()?.trim()
                if (!t.isNullOrEmpty()) input.setText(t.uppercase())
            }
        })
        root.addView(pill, lp(MATCH, dp(56)))

        val btn = Button(this).apply {
            text = "Unlock"
            setAllCaps(false)
            textSize = 17f
            setTextColor(Color.BLACK)
            typeface = Typeface.DEFAULT_BOLD
            background = bg(Color.parseColor("#F2F2F2"), 28)
            stateListAnimator = null
        }
        root.addView(btn, lp(MATCH, dp(56), top = 14))
        val status = TextView(this).apply {
            text = msg
            textSize = 15f
            setTextColor(RED)
            gravity = Gravity.CENTER
            setPadding(0, dp(16), 0, 0)
        }
        root.addView(status)
        btn.setOnClickListener {
            val key = input.text.toString().trim()
            if (key.isEmpty()) { status.text = "Enter your key"; return@setOnClickListener }
            btn.isEnabled = false
            btn.text = "Checking..."
            verify(key)
        }
        val sv = ScrollView(this).apply {
            setBackgroundColor(bgc)
            isFillViewport = true
            addView(root)
        }
        show(sv)
    }

'''

ORBIT = r'''

class OrbitView(ctx: Context) : View(ctx) {
    private val d = ctx.resources.displayMetrics.density
    private val ring = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = d
        color = Color.argb(46, 255, 255, 255)
        pathEffect = DashPathEffect(floatArrayOf(5f * d, 9f * d), 0f)
    }
    private val fill = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.parseColor("#151515") }
    private val edge = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = d
        color = Color.argb(70, 255, 255, 255)
    }
    private val dot = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE }
    private var t = 0f
    private val anim = ValueAnimator.ofFloat(0f, 1f).apply {
        duration = 70000
        repeatCount = ValueAnimator.INFINITE
        interpolator = LinearInterpolator()
        addUpdateListener { t = it.animatedValue as Float; invalidate() }
    }
    override fun onAttachedToWindow() { super.onAttachedToWindow(); anim.start() }
    override fun onDetachedFromWindow() { anim.cancel(); super.onDetachedFromWindow() }
    override fun onDraw(c: Canvas) {
        val cx = width / 2f
        val cy = height / 2f
        val base = minOf(width, height) / 2f
        val radii = floatArrayOf(0.40f, 0.64f, 0.88f)
        val counts = intArrayOf(2, 3, 4)
        val sizes = floatArrayOf(9f, 12f, 8f)
        for (ri in radii.indices) {
            val r = base * radii[ri]
            c.drawCircle(cx, cy, r, ring)
            val dir = if (ri % 2 == 0) 1 else -1
            for (j in 0 until counts[ri]) {
                val ang = Math.PI * 2 * (j.toDouble() / counts[ri] + dir * t * (4 + ri * 2))
                val x = (cx + r * Math.cos(ang)).toFloat()
                val y = (cy + r * Math.sin(ang)).toFloat()
                val sr = sizes[ri] * d
                c.drawCircle(x, y, sr, fill)
                c.drawCircle(x, y, sr, edge)
                dot.alpha = 110 + 100 * ((j + ri) % 2)
                c.drawCircle(x, y, sr * 0.28f, dot)
            }
        }
    }
}
'''

k, n = re.subn(r'    private fun showLogin\(.*?(?=    private fun verify\()', lambda m: NEW_LOGIN, k, count=1, flags=re.S)
if n != 1:
    print("❌ showLogin lama helin, waan joogsaday")
    raise SystemExit
k = k.replace("import android.animation.ValueAnimator", "import android.animation.ValueAnimator", 1)
k = k.rstrip() + "\n" + ORBIT

with open(kp, "w", encoding="utf-8") as f:
    f.write(k)
print("✅ Login cusub waa la qoray")
