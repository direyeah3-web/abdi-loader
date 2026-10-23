package com.abdi.loader

import android.content.Context
import android.util.Log
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import rikka.shizuku.Shizuku

object PatchManager {
    private const val GITHUB_API = "https://api.github.com/repos/uchihaaymane/files/releases"
    private const val TARGET_DIR = "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks/ABDI"

    fun downloadAndExtract(context: Context, onStatus: (String) -> Unit) {
        Thread {
            try {
                onStatus("Checking latest release...")
                val conn = URL(GITHUB_API).openConnection() as HttpURLConnection
                conn.setRequestProperty("Accept", "application/vnd.github.v3+json")
                conn.setRequestProperty("User-Agent", "AbdiLoader")
                conn.connectTimeout = 30000
                conn.readTimeout = 30000
                
                if (conn.responseCode != 200) {
                    onStatus("Failed to fetch release")
                    return@Thread
                }

                val response = conn.inputStream.bufferedReader().use { it.readText() }
                val jsonArray = org.json.JSONArray(response)
                var downloadUrl: String? = null
                var fileName = ""

                for (i in 0 until jsonArray.length()) {
                    val release = jsonArray.getJSONObject(i)
                    if (release.optBoolean("draft", false)) continue
                    val assets = release.optJSONArray("assets") ?: continue
                    for (j in 0 until assets.length()) {
                        val asset = assets.getJSONObject(j)
                        val name = asset.getString("name")
                        if (name.contains("pak", ignoreCase = true) && name.endsWith(".zip")) {
                            downloadUrl = asset.getString("browser_download_url")
                            fileName = name
                            break
                        }
                    }
                    if (downloadUrl != null) break
                }

                if (downloadUrl == null) {
                    onStatus("No pak.zip found in release")
                    return@Thread
                }

                onStatus("Downloading $fileName...")
                val downloadDir = android.os.Environment.getExternalStoragePublicDirectory(android.os.Environment.DIRECTORY_DOWNLOADS)
                val localFile = File(downloadDir, "abdi_patch.zip")
                
                URL(downloadUrl).openStream().use { input ->
                    FileOutputStream(localFile).use { output ->
                        input.copyTo(output)
                    }
                }

                onStatus("Writing esp_prefs.xml...")
                val prefsFile = File(context.filesDir, "esp_prefs.xml")
                FileOutputStream(prefsFile).use { it.write(getDefaultPrefs().toByteArray()) }

                onStatus("Installing patch via Shizuku...")
                if (!ShizukuEngine.checkStatus()) {
                    onStatus("Error: Shizuku permission not granted.")
                    return@Thread
                }

                val paths = listOf(
                    "$TARGET_DIR/esp_prefs.xml",
                    "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks/esp_prefs.xml",
                    "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/esp_prefs.xml",
                    "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Config/Android/esp_prefs.xml"
                )

                val cmd = StringBuilder()
                cmd.append("mkdir -p $TARGET_DIR && ")
                cmd.append("cp ${localFile.absolutePath} /data/local/tmp/abdi_patch.zip && ")
                cmd.append("unzip -o /data/local/tmp/abdi_patch.zip -d $TARGET_DIR && ")
                
                for (p in paths) {
                    cmd.append("mkdir -p $(dirname $p) && cp ${prefsFile.absolutePath} $p && chmod 777 $p && ")
                }
                cmd.append("chmod -R 777 $TARGET_DIR && rm /data/local/tmp/abdi_patch.zip")

                val process = Shizuku.newProcess(arrayOf("sh", "-c", cmd.toString()), null, null)
                val exitCode = process.waitFor()
                
                if (exitCode == 0) {
                    onStatus("FIX SUCCESSFUL. OPEN THE GAME.")
                } else {
                    val error = process.errorStream.bufferedReader().readText()
                    onStatus("Shizuku Error: $error")
                }

            } catch (e: Exception) {
                Log.e("PatchManager", "Error", e)
                onStatus("Error: ${e.message}")
            }
        }.start()
    }

    private fun getDefaultPrefs(): String {
        return """<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="line_esp" value="true" />
    <boolean name="radar_map" value="false" />
    <boolean name="skeleton" value="true" />
    <boolean name="warning_360" value="true" />
    <boolean name="aiming_at_me_warning" value="true" />
    <boolean name="vehicle" value="true" />
    <boolean name="name" value="true" />
    <boolean name="distance" value="true" />
    <boolean name="health" value="true" />
    <boolean name="weapons" value="true" />
    <boolean name="team_number" value="true" />
    <boolean name="esp_defaults_applied" value="true" />
</map>"""
    }
}
