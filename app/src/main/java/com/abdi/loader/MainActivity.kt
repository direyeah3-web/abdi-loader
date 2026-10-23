package com.abdi.loader

import android.app.Activity
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.provider.Settings
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.*
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : Activity() {
    private val base = "https://qnbiqgntqhzromwnmyth.supabase.co"
    private val anon = "sb_publishable_-jVYtd4Psza1wjuBe8g3CQ_kjxRB4lL"
    private val BLUE = Color.parseColor("#0A84FF")
    private val CARD = Color.parseColor("#1C1C1E")
    private val MUTED = Color.parseColor("#8E8E93")
    private val GREEN = Color.parseColor("#30D158")
    private val RED = Color.parseColor("#FF453A")
    private lateinit var device: String
    private var curKey = ""

    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun bg(color: Int, r: Int) = GradientDrawable().apply { setColor(color); cornerRadius = dp(r).toFloat() }
    private fun lp(w: Int, h: Int, top: Int = 0, bottom: Int = 0) =
        LinearLayout.LayoutParams(w, h).apply { topMargin = dp(top); bottomMargin = dp(bottom) }
    private fun show(v: View) {
        setContentView(v)
        v.alpha = 0f
        v.animate().alpha(1f).setDuration(320).start()
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
        val t = TextView(this).apply {
            text = "Waa la hubinayaa..."
            textSize = 16f
            setTextColor(MUTED)
            gravity = Gravity.CENTER
            setBackgroundColor(Color.BLACK)
        }
        show(t)
    }

    private fun showLogin(msg: String, prefill: String) {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.BLACK)
            setPadding(dp(28), dp(28), dp(28), dp(28))
        }
        val title = TextView(this).apply {
            text = "Abdi Loader"; textSize = 34f; setTextColor(Color.WHITE)
            typeface = Typeface.DEFAULT_BOLD; gravity = Gravity.CENTER
        }
        val sub = TextView(this).apply {
            text = "Geli license key-gaaga"; textSize = 16f; setTextColor(MUTED)
            gravity = Gravity.CENTER; setPadding(0, dp(6), 0, dp(28))
        }
        val input = EditText(this).apply {
            hint = "XXXX-XXXX-XXXX-XXXX"; setHintTextColor(Color.parseColor("#48484A"))
            setTextColor(Color.WHITE); textSize = 17f; typeface = Typeface.MONOSPACE
            gravity = Gravity.CENTER; background = bg(CARD, 16)
            setPadding(dp(18), dp(16), dp(18), dp(16)); setSingleLine(true)
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
            setText(prefill)
        }
        val btn = Button(this).apply {
            text = "Gal"; setAllCaps(false); textSize = 17f; setTextColor(Color.WHITE)
            typeface = Typeface.DEFAULT_BOLD; background = bg(BLUE, 28); stateListAnimator = null
        }
        val status = TextView(this).apply {
            text = msg; textSize = 15f; setTextColor(RED); gravity = Gravity.CENTER
            setPadding(0, dp(16), 0, 0)
        }
        btn.setOnClickListener {
            val key = input.text.toString().trim()
            if (key.isEmpty()) { status.text = "Geli key-gaaga"; return@setOnClickListener }
            btn.isEnabled = false; btn.text = "Waa la hubinayaa..."
            verify(key)
        }
        root.addView(title)
        root.addView(sub)
        root.addView(input, lp(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        root.addView(btn, lp(ViewGroup.LayoutParams.MATCH_PARENT, dp(56), top = 14))
        root.addView(status)
        show(root)
    }

    private fun verify(key: String) {
        Thread {
            val r: JSONObject? = try { call(key) } catch (e: Exception) { null }
            runOnUiThread {
                when {
                    r == null -> showLogin("Khalad network: isku day mar kale", key)
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

    private fun showDashboard(r: JSONObject) {
        val games = r.optJSONArray("games")
        val exp = if (r.isNull("expires_at")) "Weligeed" else r.optString("expires_at").take(10)
        val col = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(22), dp(40), dp(22), dp(40))
        }
        val head = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        val title = TextView(this).apply {
            text = "Games"; textSize = 32f; setTextColor(Color.WHITE); typeface = Typeface.DEFAULT_BOLD
        }
        val out = TextView(this).apply {
            text = "Logout"; textSize = 15f; setTextColor(BLUE); setPadding(dp(12), dp(8), dp(4), dp(8))
            setOnClickListener { prefs().edit().remove("key").apply(); curKey = ""; showLogin("", "") }
        }
        head.addView(title, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        head.addView(out)
        col.addView(head)
        col.addView(TextView(this).apply {
            text = "Key dhacaya: $exp"; textSize = 14f; setTextColor(MUTED); setPadding(0, dp(4), 0, dp(22))
        })

        val n = games?.length() ?: 0
        if (n == 0) {
            col.addView(TextView(this).apply {
                text = "Wali ciyaar lama darin"; textSize = 16f; setTextColor(MUTED); gravity = Gravity.CENTER
                setPadding(0, dp(40), 0, dp(40))
            })
        }
        for (i in 0 until n) {
            val g = games!!.getJSONObject(i)
            val name = g.optString("name")
            val pkg = g.optString("package")
            val launch = packageManager.getLaunchIntentForPackage(pkg)
            val row = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL
                background = bg(CARD, 20); setPadding(dp(18), dp(16), dp(14), dp(16))
            }
            val info = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
            info.addView(TextView(this).apply {
                text = name; textSize = 17f; setTextColor(Color.WHITE); typeface = Typeface.DEFAULT_BOLD
            })
            info.addView(TextView(this).apply {
                text = if (launch != null) "Rakiban" else "Ma rakiban"
                textSize = 13f; setTextColor(if (launch != null) GREEN else MUTED); setPadding(0, dp(3), 0, 0)
            })
            val go = Button(this).apply {
                text = "Fur"; setAllCaps(false); textSize = 15f; setTextColor(Color.WHITE)
                typeface = Typeface.DEFAULT_BOLD; stateListAnimator = null
                background = bg(if (launch != null) BLUE else Color.parseColor("#2C2C2E"), 22)
                isEnabled = launch != null
                setOnClickListener {
                    try { startActivity(launch) } catch (e: Exception) {
                        Toast.makeText(this@MainActivity, "Lama furi karo", Toast.LENGTH_SHORT).show()
                    }
                }
            }
            row.addView(info, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
            row.addView(go, LinearLayout.LayoutParams(dp(84), dp(44)))
            col.addView(row, lp(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT, bottom = 12))
        }
        col.addView(TextView(this).apply {
            text = "Cusbooneysii"; textSize = 15f; setTextColor(BLUE); gravity = Gravity.CENTER
            setPadding(0, dp(18), 0, dp(18))
            setOnClickListener { showLoading(); verify(curKey) }
        })
        val sv = ScrollView(this).apply { setBackgroundColor(Color.BLACK); isFillViewport = true; addView(col) }
        show(sv)
    }

    private fun errText(e: String) = when (e) {
        "invalid_key" -> "Key khalad ah"
        "inactive" -> "Key-gan waa la damiyay"
        "expired" -> "Key-gan wuu dhacay"
        "device_limit" -> "Xadka aaladaha waa buuxaa"
        "banned" -> "Akoonkan waa la xiray"
        else -> "Khalad aan la aqoon"
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
