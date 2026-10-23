KT = r'''package com.abdi.loader

import android.animation.ValueAnimator
import android.app.Activity
import android.content.ClipboardManager
import android.content.Context
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
        window.statusBarColor = Color.BLACK
        window.navigationBarColor = Color.BLACK
        device = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown-device"
        val saved = prefs().getString("key", "") ?: ""
        if (saved.isNotEmpty()) { showLoading(); verify(saved) } else showLogin("", "")
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
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setBackgroundColor(Color.parseColor("#050505"))
            setPadding(dp(26), dp(110), dp(26), dp(26))
        }
        root.addView(DotsView(this), lp(dp(56), dp(56)))
        root.addView(TextView(this).apply {
            text = "Welcome back"
            textSize = 30f
            setTextColor(Color.WHITE)
            typeface = Typeface.SERIF
            gravity = Gravity.CENTER
            setPadding(0, dp(14), 0, dp(44))
        })
        root.addView(TextView(this).apply {
            text = "License key"
            textSize = 14f
            setTextColor(Color.WHITE)
            setPadding(dp(4), 0, 0, dp(8))
        }, lp(MATCH, WRAP))

        val frame = FrameLayout(this)
        val input = EditText(this).apply {
            hint = "XXXX-XXXX-XXXX-XXXX"
            setHintTextColor(Color.parseColor("#48484A"))
            setTextColor(Color.WHITE)
            textSize = 17f
            typeface = Typeface.MONOSPACE
            gravity = Gravity.CENTER_VERTICAL
            background = bg(Color.parseColor("#141414"), 28, Color.parseColor("#262626"))
            setPadding(dp(20), dp(8), dp(78), dp(8))
            setSingleLine(true)
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
            setText(prefill)
        }
        frame.addView(input, FrameLayout.LayoutParams(MATCH, dp(56)))
        val paste = TextView(this).apply {
            text = "Paste"
            textSize = 14f
            setTextColor(BLUE)
            setPadding(dp(14), dp(10), dp(18), dp(10))
            setOnClickListener {
                val cm = this@MainActivity.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val t = cm.primaryClip?.getItemAt(0)?.coerceToText(this@MainActivity)?.toString()?.trim()
                if (!t.isNullOrEmpty()) input.setText(t.uppercase())
            }
        }
        frame.addView(paste, FrameLayout.LayoutParams(WRAP, WRAP, Gravity.END or Gravity.CENTER_VERTICAL))
        root.addView(frame, lp(MATCH, WRAP))

        val btn = Button(this).apply {
            text = "Sign In"
            setAllCaps(false)
            textSize = 17f
            setTextColor(Color.BLACK)
            typeface = Typeface.DEFAULT_BOLD
            background = bg(Color.WHITE, 28)
            stateListAnimator = null
        }
        root.addView(btn, lp(MATCH, dp(56), top = 40))
        val status = TextView(this).apply {
            text = msg
            textSize = 15f
            setTextColor(RED)
            gravity = Gravity.CENTER
            setPadding(0, dp(18), 0, 0)
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
            setBackgroundColor(Color.parseColor("#050505"))
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
                        prefs().edit().putString("key", key).apply()
                        showDashboard(r)
                    }
                    else -> showLogin(errText(r.optString("error")), key)
                }
            }
        }.start()
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
                prefs().edit().remove("key").apply()
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
                    try { startActivity(launch) } catch (e: Exception) {
                        Toast.makeText(this@MainActivity, "Could not open", Toast.LENGTH_SHORT).show()
                    }
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
        val sv = ScrollView(this).apply {
            setBackgroundColor(Color.BLACK)
            isFillViewport = true
            addView(col)
        }
        show(sv)
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
'''

with open("app/src/main/java/com/abdi/loader/MainActivity.kt", "w", encoding="utf-8") as f:
    f.write(KT)
print("✅ UI cusub waa la qoray")
