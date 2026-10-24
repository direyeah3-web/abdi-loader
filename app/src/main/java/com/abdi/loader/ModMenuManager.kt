package com.abdi.loader

import android.content.Context
import rikka.shizuku.Shizuku
import org.json.JSONObject

object ModMenuManager {
    private const val TARGET_JSON = "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks/WOLF/lexus_config.json"

    fun toggleFeature(context: Context, feature: String, enable: Boolean, onResult: (String) -> Unit) {
        if (!ShizukuEngine.checkStatus()) {
            onResult("Shizuku not connected")
            return
        }

        Thread {
            try {
                val readCmd = "cat $TARGET_JSON 2>/dev/null || echo '{}'"
                val readProc = Shizuku.newProcess(arrayOf("sh", "-c", readCmd), null, null)
                val currentJsonStr = readProc.inputStream.bufferedReader().readText().trim()
                readProc.waitFor()

                val json = if (currentJsonStr.startsWith("{")) JSONObject(currentJsonStr) else JSONObject()
                json.put(feature, enable)
                val newJsonStr = json.toString()

                val base64Str = android.util.Base64.encodeToString(newJsonStr.toByteArray(), android.util.Base64.NO_WRAP)
                val writeCmd = "echo '$base64Str' | base64 -d > $TARGET_JSON && chmod 777 $TARGET_JSON"
                val writeProc = Shizuku.newProcess(arrayOf("sh", "-c", writeCmd), null, null)
                val exitCode = writeProc.waitFor()
                
                if (exitCode == 0) {
                    onResult("Success: $feature is $enable")
                } else {
                    val error = writeProc.errorStream.bufferedReader().readText()
                    onResult("Shizuku Error: $error")
                }
            } catch (e: Exception) {
                onResult("Error: ${e.message}")
            }
        }.start()
    }
}
