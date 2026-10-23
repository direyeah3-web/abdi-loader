package com.abdi.loader

import android.content.Context
import rikka.shizuku.Shizuku
import java.io.File

object ModMenuManager {
    private const val TARGET_DIR = "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks/ABDI"

    fun toggleFeature(context: Context, feature: String, enable: Boolean, onResult: (String) -> Unit) {
        if (!ShizukuEngine.checkStatus()) {
            onResult("Shizuku not connected")
            return
        }

        val value = if (enable) "true" else "false"
        
        val paths = listOf(
            "$TARGET_DIR/esp_prefs.xml",
            "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks/esp_prefs.xml",
            "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/esp_prefs.xml",
            "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Config/Android/esp_prefs.xml"
        )

        Thread {
            try {
                val cmdBuilder = StringBuilder()
                for (p in paths) {
                    // Use sed to replace the value for the specific key
                    cmdBuilder.append("sed -i 's|name=\\\"$feature\\\" value=\\\"[a-z]*\\\"|name=\\\"$feature\\\" value=\\\"$value\\\"|g' $p && ")
                }
                cmdBuilder.append("echo 'Done'")

                val process = Shizuku.newProcess(arrayOf("sh", "-c", cmdBuilder.toString()), null, null)
                val exitCode = process.waitFor()
                
                if (exitCode == 0) {
                    onResult("Success")
                } else {
                    val error = process.errorStream.bufferedReader().readText()
                    onResult("Error: $error")
                }
            } catch (e: Exception) {
                onResult("Error: ${e.message}")
            }
        }.start()
    }
}
