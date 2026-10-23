package com.abdi.loader

import android.content.Context
import rikka.shizuku.Shizuku

object ModMenuManager {
    private const val XML_PATH = "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks/esp_prefs.xml"

    fun toggleFeature(context: Context, feature: String, enable: Boolean, onResult: (String) -> Unit) {
        if (!ShizukuEngine.checkStatus()) {
            onResult("Shizuku not connected")
            return
        }

        val value = if (enable) "true" else "false"
        // sed command to replace value
        val cmd = "sed -i 's|<boolean name=\"$feature\" value=\"[a-z]*\"|<boolean name=\"$feature\" value=\"$value\"|g' $XML_PATH"
        
        Thread {
            try {
                val process = Shizuku.newProcess(arrayOf("sh", "-c", cmd), null, null)
                val exitCode = process.waitFor()
                if (exitCode == 0) {
                    onResult("Success")
                } else {
                    onResult("Error code: $exitCode")
                }
            } catch (e: Exception) {
                onResult("Error: ${e.message}")
            }
        }.start()
    }
}
