package com.abdi.loader

import android.content.Context
import android.os.Environment
import android.util.Log
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.util.zip.ZipInputStream

object PatchManager {
    private const val GITHUB_API = "https://api.github.com/repos/uchihaaymane/files/releases/latest"

    fun downloadAndExtract(context: Context, onStatus: (String) -> Unit) {
        Thread {
            try {
                onStatus("Checking latest release...")
                val conn = URL(GITHUB_API).openConnection() as HttpURLConnection
                conn.setRequestProperty("Accept", "application/vnd.github.v3+json")
                conn.setRequestProperty("User-Agent", "AbdiLoader")
                conn.connectTimeout = 15000
                conn.readTimeout = 15000
                
                if (conn.responseCode != 200) {
                    onStatus("Failed to fetch release (HTTP ${conn.responseCode})")
                    return@Thread
                }

                val response = conn.inputStream.bufferedReader().use { it.readText() }
                val json = JSONObject(response)
                val assets = json.getJSONArray("assets")
                
                var downloadUrl: String? = null
                var fileName = ""

                for (i in 0 until assets.length()) {
                    val asset = assets.getJSONObject(i)
                    val name = asset.getString("name")
                    if (name.contains("pak", ignoreCase = true) && name.endsWith(".zip")) {
                        downloadUrl = asset.getString("browser_download_url")
                        fileName = name
                        break
                    }
                }

                if (downloadUrl == null) {
                    onStatus("No pak.zip found in release")
                    return@Thread
                }

                onStatus("Downloading $fileName...")
                val patchDir = File(context.filesDir, "patch_cache")
                if (!patchDir.exists()) patchDir.mkdirs()
                val outFile = File(patchDir, fileName)

                URL(downloadUrl).openStream().use { input ->
                    FileOutputStream(outFile).use { output ->
                        input.copyTo(output)
                    }
                }

                onStatus("Extracting to ABDI folder...")
                val abdiDir = File(Environment.getExternalStorageDirectory(), "Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks/ABDI")
                if (!abdiDir.exists()) abdiDir.mkdirs()

                ZipInputStream(outFile.inputStream()).use { zis ->
                    var entry = zis.nextEntry
                    while (entry != null) {
                        if (!entry.isDirectory) {
                            val targetFile = File(abdiDir, entry.name)
                            targetFile.parentFile?.mkdirs()
                            FileOutputStream(targetFile).use { fos ->
                                zis.copyTo(fos)
                            }
                        }
                        zis.closeEntry()
                        entry = zis.nextEntry
                    }
                }

                onStatus("FIX SUCCESSFUL. OPEN THE GAME.")
            } catch (e: Exception) {
                Log.e("PatchManager", "Error", e)
                onStatus("Error: ${e.message}")
            }
        }.start()
    }
}
