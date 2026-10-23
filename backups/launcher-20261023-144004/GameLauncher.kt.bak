package com.abdi.loader

import android.app.Activity
import android.app.Dialog
import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.GradientDrawable
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import kotlin.concurrent.thread

object GameLauncher {

    // validate() waa inuu soo celiyaa null haddii license-ku sax yahay,
    // ama fariin error ah haddii kale (lagu wacayaa thread gadaal ah)
    fun launch(activity: Activity, pkg: String, validate: () -> String? = { null }) {
        val intent = activity.packageManager.getLaunchIntentForPackage(pkg)
        if (intent == null) {
            Toast.makeText(activity, "Game not installed", Toast.LENGTH_SHORT).show()
            return
        }

        val dp = activity.resources.displayMetrics.density
        val tv = TextView(activity).apply {
            text = "Checking license..."
            setTextColor(Color.WHITE)
            textSize = 16f
            gravity = Gravity.CENTER
        }
        val box = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            val p = (28 * dp).toInt()
            setPadding(p, p, p, p)
            background = GradientDrawable().apply {
                setColor(Color.parseColor("#1C1C1E"))
                cornerRadius = 24 * dp
            }
            addView(ProgressBar(activity))
            addView(tv)
        }
        val dialog = Dialog(activity).apply {
            setCancelable(false)
            window?.setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT))
            setContentView(box)
            show()
        }

        val ui = Handler(Looper.getMainLooper())
        thread {
            val err = try { validate() } catch (e: Exception) { "Connection error" }
            activity.runOnUiThread {
                if (err != null) {
                    tv.text = err
                    ui.postDelayed({ dialog.dismiss() }, 1800)
                } else {
                    tv.text = "Starting game..."
                    ui.postDelayed({
                        dialog.dismiss()
                        activity.startActivity(intent)
                    }, 1000)
                }
            }
        }
    }
}
