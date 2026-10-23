package com.abdi.loader

import android.content.Context
import android.util.Log
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.util.zip.ZipFile
import rikka.shizuku.Shizuku

object PatchManager {
    private const val GITHUB_API = "https://api.github.com/repos/uchihaaymane/files/releases"

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
                val patchDir = File(context.filesDir, "patch_cache")
                if (!patchDir.exists()) patchDir.mkdirs()
                val outFile = File(patchDir, fileName)

                URL(downloadUrl).openStream().use { input ->
                    FileOutputStream(outFile).use { output ->
                        input.copyTo(output)
                    }
                }

                onStatus("Extracting files...")
                val tempExtractDir = File(context.filesDir, "temp_extract")
                if (tempExtractDir.exists()) tempExtractDir.deleteRecursively()
                tempExtractDir.mkdirs()

                java.util.zip.ZipFile(outFile).use { zip ->
                    val entries = zip.entries()
                    while (entries.hasMoreElements()) {
                        val entry = entries.nextElement()
                        val targetFile = File(tempExtractDir, entry.name)
                        targetFile.parentFile?.mkdirs()
                        if (!entry.isDirectory) {
                            targetFile.createNewFile()
                            zip.getInputStream(entry).use { input ->
                                FileOutputStream(targetFile).use { output ->
                                    input.copyTo(output)
                                }
                            }
                        }
                    }
                }

                onStatus("Copying to ABDI folder via Shizuku...")
                val abdiDir = "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks/ABDI"
                
                if (!ShizukuEngine.checkStatus()) {
                    onStatus("Error: Shizuku permission not granted.")
                    return@Thread
                }

                // Using Shizuku to copy files
                val process = Shizuku.newProcess(arrayOf("sh", "-c", "mkdir -p $abdiDir && cp -r ${tempExtractDir.absolutePath}/* $abdiDir/ && chmod -R 777 $abdiDir"), null, null)
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
}
