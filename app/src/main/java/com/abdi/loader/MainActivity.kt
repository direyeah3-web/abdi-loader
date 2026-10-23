package com.abdi.loader

import android.content.Intent

import android.animation.ValueAnimator
import android.app.Activity
import android.content.ClipboardManager
import android.content.Context
import android.net.Uri
import android.graphics.*
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.provider.Settings
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.ViewOutlineProvider
import android.view.animation.LinearInterpolator
import android.widget.*
import android.widget.Switch
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

class DotsView(ctx: Context) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE }
    private var t = 0f
    private val anim = ValueAnimator.ofFloat(0f, 1f).apply {
        duration = 1600
        repeatCount = ValueAnimator.INFINITE
        interpolator = LinearInterpolator()
        addUpdateListener { t = it.animatedValue as Float; invalidate() }
    }
    override fun onAttachedToWindow() { super.onAttachedToWindow(); anim.start() }
    override fun onDetachedFromWindow() { anim.cancel(); super.onDetachedFromWindow() }
    override fun onDraw(c: Canvas) {
        val cx = width / 2f
        val cy = height / 2f
        val r = minOf(width, height) / 2f * 0.72f
        val n = 8
        for (i in 0 until n) {
            val a = Math.PI * 2 * i / n - Math.PI / 2
            val phase = ((t * n - i) % n + n) % n
            val k = 1f - phase / n
            p.alpha = (80 + 175 * k).toInt()
            val rad = r * 0.17f * (0.6f + 0.5f * k)
            c.drawCircle((cx + r * Math.cos(a)).toFloat(), (cy + r * Math.sin(a)).toFloat(), rad, p)
        }
    }
}

class MainActivity : Activity() {
    private val base = "https://qnbiqgntqhzromwnmyth.supabase.co"
    private val anon = "sb_publishable_-jVYtd4Psza1wjuBe8g3CQ_kjxRB4lL"
    private val BLUE = Color.parseColor("#0A84FF")
    private val CARD = Color.parseColor("#1C1C1E")
    private val MUTED = Color.parseColor("#8E8E93")
    private val GREEN = Color.parseColor("#30D158")
    private val ORANGE = Color.parseColor("#FF9F0A")
    private val RED = Color.parseColor("#FF453A")
    private val MATCH = ViewGroup.LayoutParams.MATCH_PARENT
    private val WRAP = ViewGroup.LayoutParams.WRAP_CONTENT
    private lateinit var device: String
    private var curKey = ""
    private var pendingGamePackage: String? = null
    private val obbPickerRequest = 7401

    private fun openGame(pkg: String) {
        val saved = prefs().getString("obb_tree_uri", null)
        if (!saved.isNullOrBlank()) {
            GameLauncher.launch(this, pkg, Uri.parse(saved))
            return
        }
        pendingGamePackage = pkg
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE).apply {
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
        }
        try {
            startActivityForResult(intent, obbPickerRequest)
        } catch (e: Exception) {
            pendingGamePackage = null
            Toast.makeText(this, "Cannot open folder picker: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    @Deprecated("Uses the system folder picker result")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != obbPickerRequest) return

        val pkg = pendingGamePackage
        pendingGamePackage = null
        val uri = if (resultCode == RESULT_OK) data?.data else null

        if (pkg == null) return
        if (uri == null) {
            Toast.makeText(this, "Folder selection cancelled", Toast.LENGTH_SHORT).show()
            return
        }

        try {
            val flags = data?.flags ?: 0
            contentResolver.takePersistableUriPermission(
                uri,
                flags and (Intent.FLAG_GRANT_READ_URI_PERMISSION or
                    Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            )
            prefs().edit().putString("obb_tree_uri", uri.toString()).apply()
            GameLauncher.launch(this, pkg, uri)
        } catch (e: Exception) {
            Toast.makeText(this, "Folder permission failed: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun bg(color: Int, r: Int, stroke: Int = 0): GradientDrawable = GradientDrawable().apply {
        setColor(color)
        cornerRadius = dp(r).toFloat()
        if (stroke != 0) setStroke(dp(1), stroke)
    }
    private fun lp(w: Int, h: Int, top: Int = 0, bottom: Int = 0) =
        LinearLayout.LayoutParams(w, h).apply { topMargin = dp(top); bottomMargin = dp(bottom) }
    private fun round(v: View, r: Int) {
        v.outlineProvider = object : ViewOutlineProvider() {
            override fun getOutline(view: View, outline: Outline) {
                outline.setRoundRect(0, 0, view.width, view.height, dp(r).toFloat())
            }
        }
        v.clipToOutline = true
    }
    private fun show(v: View) {
        setContentView(v)
        v.alpha = 0f
        v.animate().alpha(1f).setDuration(350).start()
    }
    private fun prefs() = getSharedPreferences("a", MODE_PRIVATE)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ShizukuEngine.init()
        window.statusBarColor = Color.BLACK
        window.navigationBarColor = Color.BLACK
        device = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown-device"
        val saved = prefs().getString("key", "") ?: ""
        if (saved.isNotEmpty()) { showLoading(); verify(saved) } else showLogin("", prefs().getString("draft", "") ?: "")
    }

    private fun showLoading() {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.BLACK)
        }
        box.addView(DotsView(this), lp(dp(48), dp(48)))
        box.addView(TextView(this).apply {
            text = "Checking license..."
            textSize = 15f
            setTextColor(MUTED)
            gravity = Gravity.CENTER
            setPadding(0, dp(18), 0, 0)
        })
        show(box)
    }

    private fun showLogin(msg: String, prefill: String) {
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
                addTextChangedListener(object : android.text.TextWatcher {
                    override fun afterTextChanged(s: android.text.Editable?) {
                        prefs().edit().putString("draft", s?.toString() ?: "").apply()
                    }
                    override fun beforeTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}
                    override fun onTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}
                })
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

    private fun verify(key: String) {
        Thread {
            val r: JSONObject? = try { call(key) } catch (e: Exception) { null }
            runOnUiThread {
                when {
                    r == null -> showLogin("Network error. Try again.", key)
                    r.optBoolean("ok") -> {
                        curKey = key
                        prefs().edit().putString("key", key).remove("draft").apply()
                        showDashboard(r)
                    }
                    else -> showLogin(errText(r.optString("error")), key)
                }
            }
        }.start()
    }

    private var bigView: TextView? = null
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

    private fun parseMs(s: String): Long? = try {
        val f = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
        f.timeZone = TimeZone.getTimeZone("UTC")
        f.parse(s.take(19))?.time
    } catch (e: Exception) { null }

    private fun showDashboard(r: JSONObject) {
        val games = r.optJSONArray("games")
        val expIso: String? = if (r.isNull("expires_at")) null else r.optString("expires_at")

        val col = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(22), dp(48), dp(22), dp(40))
        }
        val head = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        head.addView(TextView(this).apply {
            text = "Games"
            textSize = 34f
            setTextColor(Color.WHITE)
            typeface = Typeface.DEFAULT_BOLD
        }, LinearLayout.LayoutParams(0, WRAP, 1f))
        head.addView(TextView(this).apply {
            text = "Logout"
            textSize = 16f
            setTextColor(BLUE)
            setPadding(dp(12), dp(8), dp(2), dp(8))
            setOnClickListener {
                prefs().edit().remove("key").remove("draft").apply()
                curKey = ""
                showLogin("", "")
            }
        })
        col.addView(head)

        var big = "Lifetime"
        var small = "Never expires"
        var dotColor = GREEN
        if (expIso != null) {
            val ms = parseMs(expIso)
            if (ms != null) {
                val left = ms - System.currentTimeMillis()
                val days = Math.ceil(left / 86400000.0).toLong()
                small = "Expires " + SimpleDateFormat("MMM d, yyyy", Locale.ENGLISH).format(Date(ms))
                big = if (days <= 0L) "Expired" else if (days == 1L) "1 day left" else "$days days left"
                dotColor = if (days <= 3L) RED else if (days <= 7L) ORANGE else GREEN
                startTicker(ms)
            }
        }
        val card = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = bg(CARD, 24, Color.parseColor("#2C2C2E"))
            setPadding(dp(20), dp(18), dp(20), dp(20))
        }
        val tag = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val dot = View(this).apply {
            dotView = this
            background = GradientDrawable().apply { shape = GradientDrawable.OVAL; setColor(dotColor) }
        }
        tag.addView(dot, LinearLayout.LayoutParams(dp(8), dp(8)))
        tag.addView(TextView(this).apply {
            text = "LICENSE"
            textSize = 12f
            letterSpacing = 0.12f
            setTextColor(MUTED)
            setPadding(dp(8), 0, 0, 0)
        })
        card.addView(tag)
        card.addView(TextView(this).apply {
            text = big
            bigView = this
            textSize = 30f
            setTextColor(Color.WHITE)
            typeface = Typeface.DEFAULT_BOLD
            setPadding(0, dp(8), 0, 0)
        })
        card.addView(TextView(this).apply {
            text = small
            textSize = 14f
            setTextColor(MUTED)
            setPadding(0, dp(2), 0, 0)
        })
        col.addView(card, lp(MATCH, WRAP, top = 18, bottom = 26))


        // === SHIZUKU BOX ===
        val shizukuBox = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = bg(CARD, 24, Color.parseColor("#2C2C2E"))
            setPadding(dp(20), dp(18), dp(20), dp(18))
        }
        val shizukuHead = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        shizukuHead.addView(TextView(this).apply {
            text = "\uD83D\uDEE1\uFE0F"
            textSize = 24f
        })
        shizukuHead.addView(TextView(this).apply {
            text = "Shizuku ADB Engine"
            textSize = 16f
            setTextColor(Color.WHITE)
            typeface = Typeface.DEFAULT_BOLD
            setPadding(dp(12), 0, 0, 0)
        }, LinearLayout.LayoutParams(0, WRAP, 1f))
        
        val shizukuStatusBtn = TextView(this).apply {
            text = if (ShizukuEngine.checkStatus()) "CONNECTED" else "CONNECT"
            textSize = 12f
            setTextColor(if (ShizukuEngine.checkStatus()) GREEN else BLUE)
            background = bg(Color.parseColor("#1C1C1E"), 12, if (ShizukuEngine.checkStatus()) GREEN else BLUE)
            setPadding(dp(12), dp(6), dp(12), dp(6))
            setOnClickListener {
                ShizukuEngine.requestPermission()
            }
        }
        shizukuHead.addView(shizukuStatusBtn)
        shizukuBox.addView(shizukuHead)
        shizukuBox.addView(TextView(this).apply {
            text = if (ShizukuEngine.checkStatus()) "Shizuku ADB permission is active." else "Requires Shizuku app installed."
            textSize = 12f
            setTextColor(MUTED)
            setPadding(0, dp(8), 0, 0)
        })
        col.addView(shizukuBox, lp(MATCH, WRAP, bottom = 24))

        // === START ENGINE & FIST ===
        val engineBtn = Button(this).apply {
            text = "COPY FIST"
            setAllCaps(false)
            textSize = 15f
            setTextColor(Color.BLACK)
            typeface = Typeface.DEFAULT_BOLD
            background = bg(Color.parseColor("#32ADE6"), 28)
            stateListAnimator = null
            setOnClickListener {
                isEnabled = false
                text = "DOWNLOADING..."
                PatchManager.downloadAndExtract(this@MainActivity) { status ->
                    runOnUiThread {
                        Toast.makeText(this@MainActivity, status, Toast.LENGTH_LONG).show()
                        if (status.contains("SUCCESSFUL")) {
                            text = "FIX SUCCESSFUL. OPEN THE GAME."
                        } else {
                            text = "COPY FIST"
                            isEnabled = true
                        }
                    }
                }
            }
        }
        col.addView(engineBtn, lp(MATCH, dp(54), bottom = 12))

        val startBtn = Button(this).apply {
            text = "START CHEAT ENGINE"
            setAllCaps(false)
            textSize = 15f
            setTextColor(Color.BLACK)
            typeface = Typeface.DEFAULT_BOLD
            background = bg(Color.parseColor("#32ADE6"), 28)
            stateListAnimator = null
            setOnClickListener {
                if (Settings.canDrawOverlays(this@MainActivity)) {
                    startService(Intent(this@MainActivity, FloatingMenuService::class.java))
                    Toast.makeText(this@MainActivity, "Engine Started", Toast.LENGTH_SHORT).show()
                } else {
                    startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
                }
            }
        }
        col.addView(startBtn, lp(MATCH, dp(54), bottom = 12))

        // === YOUR GAMES ===
        col.addView(TextView(this).apply {
            text = "YOUR GAMES"
            textSize = 12f
            letterSpacing = 0.12f
            setTextColor(MUTED)
            setPadding(dp(4), 0, 0, dp(10))
        })

        val n = games?.length() ?: 0
        if (n == 0) {
            col.addView(TextView(this).apply {
                text = "No games available yet"
                textSize = 16f
                setTextColor(MUTED)
                gravity = Gravity.CENTER
                setPadding(0, dp(40), 0, dp(40))
            })
        }
        for (i in 0 until n) {
            val g = games!!.getJSONObject(i)
            val name = g.optString("name")
            val pkg = g.optString("package")
            val launch = packageManager.getLaunchIntentForPackage(pkg)

            val row = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                background = bg(CARD, 22)
                setPadding(dp(14), dp(14), dp(14), dp(14))
            }
            val icon: View = if (launch != null) {
                ImageView(this).apply {
                    scaleType = ImageView.ScaleType.FIT_CENTER
                    try { setImageDrawable(packageManager.getApplicationIcon(pkg)) } catch (e: Exception) { }
                }
            } else {
                TextView(this).apply {
                    text = name.take(2).uppercase()
                    textSize = 18f
                    setTextColor(MUTED)
                    typeface = Typeface.DEFAULT_BOLD
                    gravity = Gravity.CENTER
                    background = GradientDrawable(
                        GradientDrawable.Orientation.TL_BR,
                        intArrayOf(Color.parseColor("#3A3A3C"), Color.parseColor("#232325"))
                    )
                }
            }
            round(icon, 14)
            row.addView(icon, LinearLayout.LayoutParams(dp(54), dp(54)))

            val info = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(dp(14), 0, dp(8), 0)
            }
            info.addView(TextView(this).apply {
                text = name
                textSize = 16f
                setTextColor(Color.WHITE)
                typeface = Typeface.DEFAULT_BOLD
            })
            info.addView(TextView(this).apply {
                text = if (launch != null) "Installed" else "Not installed"
                textSize = 13f
                setTextColor(if (launch != null) GREEN else MUTED)
                setPadding(0, dp(3), 0, 0)
            })
            row.addView(info, LinearLayout.LayoutParams(0, WRAP, 1f))

            val go = Button(this).apply {
                text = "Open"
                setAllCaps(false)
                textSize = 15f
                setTextColor(Color.WHITE)
                typeface = Typeface.DEFAULT_BOLD
                stateListAnimator = null
                background = bg(if (launch != null) BLUE else Color.parseColor("#2C2C2E"), 22)
                isEnabled = launch != null
                setOnClickListener {
                    openGame(pkg)
                }
            }
            row.addView(go, LinearLayout.LayoutParams(dp(80), dp(42)))

            row.alpha = 0f
            row.translationY = dp(14).toFloat()
            row.animate().alpha(1f).translationY(0f).setStartDelay(i * 70L).setDuration(380).start()
            col.addView(row, lp(MATCH, WRAP, bottom = 12))
        }

        col.addView(TextView(this).apply {
            text = "Refresh"
            textSize = 15f
            setTextColor(BLUE)
            gravity = Gravity.CENTER
            setPadding(0, dp(18), 0, dp(18))
            setOnClickListener { showLoading(); verify(curKey) }
        })
        col.addView(TextView(this).apply {
            text = "Log"
            textSize = 15f
            setTextColor(MUTED)
            gravity = Gravity.CENTER
            setPadding(0, dp(10), 0, dp(18))
            setOnClickListener { DebugLog.show(this@MainActivity) }
        })

        // === BOTTOM TAB BAR ===
        val tabBar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            background = bg(Color.parseColor("#101010"), 0, Color.parseColor("#2C2C2E"))
            setPadding(0, dp(12), 0, dp(12))
            gravity = Gravity.CENTER
        }
        val homeTab = TextView(this).apply {
            text = "Home"
            textSize = 15f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            setPadding(0, dp(8), 0, dp(8))
            setOnClickListener { showDashboard(r) }
        }
        val settingsTab = TextView(this).apply {
            text = "Settings"
            textSize = 15f
            setTextColor(MUTED)
            gravity = Gravity.CENTER
            setPadding(0, dp(8), 0, dp(8))
            setOnClickListener { showSettings() }
        }
        tabBar.addView(homeTab, LinearLayout.LayoutParams(0, WRAP, 1f))
        tabBar.addView(settingsTab, LinearLayout.LayoutParams(0, WRAP, 1f))
        
        // Main wrapper: ScrollView on top, TabBar on bottom
        val mainWrapper = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.BLACK)
        }
        val scrollView = ScrollView(this).apply {
            isFillViewport = true
            addView(col)
        }
        mainWrapper.addView(scrollView, LinearLayout.LayoutParams(MATCH, 0, 1f))
        mainWrapper.addView(tabBar, LinearLayout.LayoutParams(MATCH, WRAP))
        
        show(mainWrapper)
    }


    
    private fun showSettings() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.BLACK)
        }
        val sv = ScrollView(this).apply {
            isFillViewport = true
            setPadding(dp(22), dp(48), dp(22), dp(24))
        }
        val col = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
        }
        sv.addView(col)

        col.addView(TextView(this).apply {
            text = "Settings"
            textSize = 34f
            setTextColor(Color.WHITE)
            typeface = Typeface.DEFAULT_BOLD
            setPadding(0, 0, 0, dp(24))
        })

        fun addSection(title: String) {
            col.addView(TextView(this).apply {
                text = title
                textSize = 12f
                letterSpacing = 0.12f
                setTextColor(MUTED)
                setPadding(dp(16), dp(16), 0, dp(8))
            })
        }

        fun addRow(title: String, value: String? = null, isSwitch: Boolean = false) {
            val row = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                background = bg(CARD, 12)
                setPadding(dp(16), dp(14), dp(16), dp(14))
            }
            row.addView(TextView(this).apply {
                text = title
                textSize = 16f
                setTextColor(Color.WHITE)
            }, LinearLayout.LayoutParams(0, WRAP, 1f))
            
            if (isSwitch) {
                row.addView(android.widget.Switch(this).apply {
                    isChecked = true
                    setOnCheckedChangeListener { _, _ -> }
                })
            } else if (value != null) {
                row.addView(TextView(this).apply {
                    text = value
                    textSize = 16f
                    setTextColor(MUTED)
                })
            }
            col.addView(row, lp(MATCH, WRAP, bottom = 1))
        }

        addSection("ACCOUNT")
        addRow("Profile", "user@abdi.loader")
        addRow("License Key", "Active")

        addSection("APPEARANCE")
        addRow("Dark Mode", isSwitch = true)

        addSection("LANGUAGE")
        addRow("Language", "English")

        addSection("NOTIFICATIONS")
        addRow("Push Notifications", isSwitch = true)

        addSection("ABOUT")
        addRow("Version", "1.0.0")
        addRow("Developer", "direyeah3-web")

        // Bottom Tab Bar for Settings
        val tabBar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            background = bg(Color.parseColor("#101010"), 0, Color.parseColor("#2C2C2E"))
            setPadding(0, dp(12), 0, dp(12))
            gravity = Gravity.CENTER
        }
        val homeTab = TextView(this).apply {
            text = "Home"
            textSize = 15f
            setTextColor(MUTED)
            gravity = Gravity.CENTER
            setPadding(0, dp(8), 0, dp(8))
            setOnClickListener { verify(curKey) }
        }
        val settingsTab = TextView(this).apply {
            text = "Settings"
            textSize = 15f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            setPadding(0, dp(8), 0, dp(8))
        }
        tabBar.addView(homeTab, LinearLayout.LayoutParams(0, WRAP, 1f))
        tabBar.addView(settingsTab, LinearLayout.LayoutParams(0, WRAP, 1f))

        root.addView(sv, LinearLayout.LayoutParams(MATCH, 0, 1f))
        root.addView(tabBar, LinearLayout.LayoutParams(MATCH, WRAP))
        show(root)
    }

    private fun errText(e: String) = when (e) {
        "invalid_key" -> "Invalid key"
        "inactive" -> "This key has been deactivated"
        "expired" -> "This key has expired"
        "device_limit" -> "Device limit reached"
        "banned" -> "This account has been banned"
        else -> "Something went wrong"
    }

    private fun call(key: String): JSONObject {
        val c = URL("$base/rest/v1/rpc/get_games").openConnection() as HttpURLConnection
        c.requestMethod = "POST"
        c.connectTimeout = 10000
        c.readTimeout = 10000
        c.setRequestProperty("apikey", anon)
        c.setRequestProperty("Content-Type", "application/json")
        c.doOutput = true
        val body = JSONObject().put("p_key", key).put("p_device", device).toString()
        c.outputStream.use { it.write(body.toByteArray()) }
        val stream = if (c.responseCode in 200..299) c.inputStream else c.errorStream
        val text = stream.bufferedReader().use { it.readText() }
        return JSONObject(text)
    }
}


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
