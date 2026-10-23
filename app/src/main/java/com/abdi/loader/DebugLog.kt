package com.abdi.loader

import android.app.Activity
import android.app.AlertDialog
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

object DebugLog {
    fun read(): String = try {
        val p = Runtime.getRuntime().exec(arrayOf("logcat", "-d", "-t", "2000"))
        val all = p.inputStream.bufferedReader().readLines()
        val keys = listOf("FATAL", "AndroidRuntime", "SIGSEGV", "SIGABRT",
            "Fatal signal", "BlackBox", "tencent", "Exception", "died", "Killing")
        val f = all.filter { l -> keys.any { l.contains(it, true) } }
        (if (f.isEmpty()) all else f).takeLast(60).joinToString("\n")
    } catch (e: Exception) {
        "Log error: $e"
    }

    fun show(a: Activity) {
        val txt = read()
        val tv = TextView(a).apply {
            text = txt; textSize = 10f
            setTextIsSelectable(true); setPadding(24, 24, 24, 24)
        }
        AlertDialog.Builder(a)
            .setTitle("Debug log")
            .setView(ScrollView(a).apply { addView(tv) })
            .setPositiveButton("Copy") { _, _ ->
                val cm = a.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                cm.setPrimaryClip(ClipData.newPlainText("log", txt))
                Toast.makeText(a, "Copied", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Close", null)
            .show()
    }
}
