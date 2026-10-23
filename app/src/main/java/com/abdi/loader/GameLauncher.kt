package com.abdi.loader

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.util.Log
import android.widget.Toast

object GameLauncher {
    fun launch(activity: Activity, pkg: String, treeUri: Uri?, validate: () -> String? = { null }) {
        val error = validate()
        if (error != null) {
            Toast.makeText(activity, error, Toast.LENGTH_LONG).show()
            return
        }
        try {
            val intent = activity.packageManager.getLaunchIntentForPackage(pkg)
            if (intent == null) {
                Toast.makeText(activity, "Game is not installed: $pkg", Toast.LENGTH_LONG).show()
                return
            }
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            activity.startActivity(intent)
        } catch (e: Exception) {
            Log.e("AbdiLoader", "launch failed", e)
            Toast.makeText(activity, "Launch failed: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }
}
