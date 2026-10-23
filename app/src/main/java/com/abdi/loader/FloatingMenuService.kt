package com.abdi.loader

import android.app.Service
import android.content.Intent
import android.graphics.PixelFormat
import android.os.IBinder
import android.view.Gravity
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.Switch
import android.widget.TextView

class FloatingMenuService : Service() {
    private lateinit var windowManager: WindowManager
    private lateinit var floatingView: LinearLayout

    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        
        floatingView = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(0xCC000000.toInt())
            setPadding(20, 20, 20, 20)
            
            val title = TextView(this@FloatingMenuService).apply {
                text = "ABDI MENU"
                setTextColor(0xFF32ADE6.toInt())
                textSize = 18f
            }
            addView(title)

            val features = listOf("line_esp", "radar_map", "skeleton", "vehicle", "warning_360", "aiming_at_me_warning")
            for (feature in features) {
                val switch = Switch(this@FloatingMenuService).apply {
                    text = feature.replace("_", " ").capitalize()
                    setTextColor(0xFFFFFFFF.toInt())
                    setOnCheckedChangeListener { _, isChecked ->
                        ModMenuManager.toggleFeature(this@FloatingMenuService, feature, isChecked) { _ -> }
                    }
                }
                addView(switch)
            }
            
            val closeBtn = Button(this@FloatingMenuService).apply {
                text = "Close Menu"
                setOnClickListener { stopSelf() }
            }
            addView(closeBtn)
        }

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 50
            y = 200
        }
        windowManager.addView(floatingView, params)
    }

    override fun onDestroy() {
        super.onDestroy()
        if (::floatingView.isInitialized) windowManager.removeView(floatingView)
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
