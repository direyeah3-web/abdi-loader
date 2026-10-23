package com.abdi.loader

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.provider.Settings
import android.text.InputType
import android.view.Gravity
import android.widget.*
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : Activity() {
    private val base = "https://qnbiqgntqhzromwnmyth.supabase.co"
    private val anon = "sb_publishable_-jVYtd4Psza1wjuBe8g3CQ_kjxRB4lL"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val pad = (24 * resources.displayMetrics.density).toInt()
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.BLACK)
            setPadding(pad, pad, pad, pad)
        }
        val title = TextView(this).apply {
            text = "Abdi Loader"
            textSize = 30f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
        }
        val input = EditText(this).apply {
            hint = "License key"
            setHintTextColor(Color.GRAY)
            setTextColor(Color.WHITE)
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS
            setText(getSharedPreferences("a", MODE_PRIVATE).getString("key", ""))
        }
        val btn = Button(this).apply { text = "Hubi key-ga" }
        val status = TextView(this).apply {
            textSize = 16f
            setTextColor(Color.LTGRAY)
            gravity = Gravity.CENTER
            setPadding(0, pad, 0, 0)
        }
        root.addView(title)
        root.addView(input)
        root.addView(btn)
        root.addView(status)
        setContentView(root)

        val device = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown-device"
        btn.setOnClickListener {
            val key = input.text.toString().trim()
            status.text = "Waa la hubinayaa..."
            btn.isEnabled = false
            Thread {
                val msg = try { check(key, device) } catch (e: Exception) { "Khalad network: isku day mar kale" }
                runOnUiThread {
                    status.text = msg
                    btn.isEnabled = true
                }
            }.start()
        }
    }

    private fun check(key: String, device: String): String {
        val c = URL("$base/rest/v1/rpc/validate_key").openConnection() as HttpURLConnection
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
        val j = JSONObject(text)
        if (j.optBoolean("ok")) {
            getSharedPreferences("a", MODE_PRIVATE).edit().putString("key", key).apply()
            return "Key waa sax"
        }
        return when (j.optString("error")) {
            "invalid_key" -> "Key khalad ah"
            "inactive" -> "Key-gan waa la damiyay"
            "expired" -> "Key-gan wuu dhacay"
            "device_limit" -> "Xadka aaladaha waa buuxaa"
            "banned" -> "Akoonkan waa la xiray"
            else -> "Khalad aan la aqoon"
        }
    }
}
