from pathlib import Path
from datetime import datetime
import re

root = Path.home() / "abdi-loader"
manifest = root / "app/src/main/AndroidManifest.xml"
launcher = root / "app/src/main/java/com/abdi/loader/GameLauncher.kt"

for p in (manifest, launcher):
    if not p.exists():
        raise SystemExit(f"File lama helin: {p}")

backup = root / "backups" / ("obb-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
backup.mkdir(parents=True, exist_ok=True)

for p in (manifest, launcher):
    (backup / p.name).write_text(p.read_text())

m = manifest.read_text()
if "android.permission.MANAGE_EXTERNAL_STORAGE" not in m:
    pos = re.search(r"<application\b", m)
    if not pos:
        raise SystemExit("AndroidManifest.xml: <application> lama helin")
    m = m[:pos.start()] + \
        '    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" />\n' + m[pos.start():]
manifest.write_text(m)

launcher.write_text(r'''package com.abdi.loader

import android.app.Activity
import android.app.ProgressDialog
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.Settings
import android.util.Log
import android.widget.Toast
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.io.IOException
import top.niunaijun.blackbox.BlackBoxCore
import top.niunaijun.blackbox.core.env.BEnvironment

object GameLauncher {
    fun launch(activity: Activity, pkg: String, validate: () -> String? = { null }) {
        val error = validate()
        if (error != null) {
            Toast.makeText(activity, error, Toast.LENGTH_LONG).show()
            return
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R &&
            !Environment.isExternalStorageManager()) {
            Toast.makeText(
                activity,
                "Allow All files access for Abdi Loader, then tap Open again.",
                Toast.LENGTH_LONG
            ).show()
            try {
                activity.startActivity(
                    Intent(
                        Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION,
                        Uri.parse("package:${activity.packageName}")
                    )
                )
            } catch (e: Exception) {
                try {
                    activity.startActivity(
                        Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION)
                    )
                } catch (ignored: Exception) {
                    Log.e("AbdiLoader", "Cannot open storage settings", e)
                }
            }
            return
        }

        val dialog = ProgressDialog(activity).apply {
            setTitle("Abdi Loader")
            setMessage("Preparing PUBG...")
            setProgressStyle(ProgressDialog.STYLE_HORIZONTAL)
            max = 100
            progress = 0
            setCancelable(false)
            show()
        }

        Thread {
            try {
                val core = BlackBoxCore.get()
                val userId = 0

                if (!core.isInstalled(pkg, userId)) {
                    val result = core.installPackageAsUser(pkg, userId)
                    if (!core.isInstalled(pkg, userId)) {
                        throw IOException("Virtual installation failed: $result")
                    }
                }

                val source = File(
                    Environment.getExternalStorageDirectory(),
                    "Android/obb/$pkg"
                )
                val destination = BEnvironment.getExternalObbDir(pkg, userId)

                copyObb(source, destination) { percent ->
                    activity.runOnUiThread {
                        if (dialog.isShowing) {
                            dialog.progress = percent
                            dialog.setMessage("Copying OBB... $percent%")
                        }
                    }
                }

                activity.runOnUiThread {
                    if (dialog.isShowing) {
                        dialog.progress = 100
                        dialog.setMessage("OBB copied. Launching game...")
                    }
                }

                if (!core.launchApk(pkg, userId)) {
                    throw IOException("Virtual engine could not launch $pkg")
                }

                activity.runOnUiThread {
                    if (dialog.isShowing) dialog.dismiss()
                    Toast.makeText(
                        activity, "OBB copy finished. Launch started.",
                        Toast.LENGTH_LONG
                    ).show()
                }
            } catch (e: Exception) {
                Log.e("AbdiLoader", "OBB copy / virtual launch failed", e)
                activity.runOnUiThread {
                    if (dialog.isShowing) dialog.dismiss()
                    Toast.makeText(
                        activity,
                        "Loader error: ${e.message}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
        }.start()
    }

    private fun copyObb(
        source: File,
        destination: File,
        update: (Int) -> Unit
    ) {
        val files = if (source.exists()) {
            source.walkTopDown().filter { it.isFile }.toList()
        } else {
            emptyList()
        }

        val alreadyCopied = destination.exists() &&
            destination.walkTopDown().any { it.isFile }

        if (files.isEmpty()) {
            if (alreadyCopied) {
                update(100)
                return
            }
            throw IOException(
                "PUBG OBB folder not found: ${source.absolutePath}. " +
                "Open PUBG normally and ensure its game files are downloaded."
            )
        }

        val total = files.sumOf { it.length() }
        if (total <= 0L) throw IOException("PUBG OBB folder is empty")

        if (!destination.exists() && !destination.mkdirs()) {
            throw IOException("Cannot create virtual OBB folder")
        }

        var copied = 0L
        var lastPercent = -1

        fun report() {
            val percent = ((copied * 100L) / total).toInt().coerceIn(0, 100)
            if (percent != lastPercent) {
                lastPercent = percent
                update(percent)
            }
        }

        for (file in files) {
            val relative = file.absolutePath
                .removePrefix(source.absolutePath)
                .trimStart(File.separatorChar)
            val output = File(destination, relative)

            if (output.exists() &&
                output.length() == file.length() &&
                output.lastModified() >= file.lastModified()) {
                copied += file.length()
                report()
                continue
            }

            output.parentFile?.mkdirs()

            FileInputStream(file).use { input ->
                FileOutputStream(output).use { out ->
                    val buffer = ByteArray(1024 * 1024)
                    while (true) {
                        val n = input.read(buffer)
                        if (n < 0) break
                        out.write(buffer, 0, n)
                        copied += n
                        report()
                    }
                }
            }
            output.setLastModified(file.lastModified())
        }

        update(100)
    }
}
''')

print("OBB support added.")
print("Backup:", backup)
print("Next: git push this patch to GitHub Actions.")
