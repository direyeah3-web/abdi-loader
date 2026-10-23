import os, shutil
p = "app/src/main/java/com/abdi/loader/ObbManager.kt"
if os.path.exists(p):
    shutil.copy(p, p + ".bak")
code = r"""package com.abdi.loader

import android.app.Activity
import android.app.AlertDialog
import android.app.ProgressDialog
import android.content.Intent
import android.net.Uri
import android.provider.OpenableColumns
import android.util.Log
import android.widget.Toast
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import top.niunaijun.blackbox.core.env.BEnvironment

object ObbManager {
    const val REQ_PICK_OBB = 7421
    private var pendingPkg: String? = null
    private var pendingAfter: (() -> Unit)? = null

    fun obbDir(pkg: String): File = BEnvironment.getExternalObbDir(pkg, 0)

    fun isReady(pkg: String): Boolean {
        return try {
            val d = obbDir(pkg)
            d.exists() && d.walkTopDown().any { it.isFile && it.extension.equals("obb", true) }
        } catch (e: Exception) {
            false
        }
    }

    private fun dlg(a: Activity) =
        AlertDialog.Builder(a, android.R.style.Theme_DeviceDefault_Dialog_Alert)

    fun showFailed(a: Activity, pkg: String, reason: String?, after: (() -> Unit)? = null) {
        pendingPkg = pkg
        pendingAfter = after
        val why = reason ?: "The OBB file is missing or could not be read."
        dlg(a).setTitle("OBB Copy Failed")
            .setMessage(why + "\n\nDo you want to choose the OBB file manually?")
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Choose File") { _, _ -> pickFile(a) }
            .show()
    }

    private fun pickFile(a: Activity) {
        val i = Intent(Intent.ACTION_OPEN_DOCUMENT)
        i.addCategory(Intent.CATEGORY_OPENABLE)
        i.type = "*/*"
        a.startActivityForResult(i, REQ_PICK_OBB)
    }

    // Ka wac MainActivity.onActivityResult
    fun handleResult(a: Activity, requestCode: Int, resultCode: Int, data: Intent?): Boolean {
        if (requestCode != REQ_PICK_OBB) return false
        val pkg = pendingPkg ?: return true
        val uri = data?.data
        if (resultCode != Activity.RESULT_OK || uri == null) return true
        val info = queryInfo(a, uri)
        val name = info.first
        val size = info.second
        if (!name.endsWith(".obb", true) || !name.contains(pkg)) {
            Toast.makeText(a, "Wrong file. Select main.<version>.$pkg.obb", Toast.LENGTH_LONG).show()
            return true
        }
        dlg(a).setTitle("Import this OBB?")
            .setMessage(
                "The selected file will be copied into your game's storage.\n\n" +
                name + "\n" + fmtSize(size)
            )
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Copy OBB") { _, _ -> copy(a, pkg, uri, name, size) }
            .show()
        return true
    }

    private fun queryInfo(a: Activity, uri: Uri): Pair<String, Long> {
        var name = "file.obb"
        var size = 0L
        a.contentResolver.query(uri, null, null, null, null)?.use { c ->
            if (c.moveToFirst()) {
                val ni = c.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                val si = c.getColumnIndex(OpenableColumns.SIZE)
                if (ni >= 0) name = c.getString(ni) ?: name
                if (si >= 0) size = c.getLong(si)
            }
        }
        return Pair(name, size)
    }

    private fun fmtSize(b: Long): String {
        if (b <= 0L) return "Unknown size"
        val gb = b / 1073741824.0
        return if (gb >= 1.0) String.format("%.2f GB", gb)
        else String.format("%.0f MB", b / 1048576.0)
    }

    private fun copy(a: Activity, pkg: String, uri: Uri, name: String, size: Long) {
        val pd = ProgressDialog(a)
        pd.setTitle("Abdi Loader")
        pd.setMessage("Copying OBB... 0%")
        pd.setProgressStyle(ProgressDialog.STYLE_HORIZONTAL)
        pd.max = 100
        pd.setCancelable(false)
        pd.show()
        Thread {
            var out: File? = null
            try {
                val dest = obbDir(pkg)
                if (!dest.exists() && !dest.mkdirs()) throw IOException("Cannot create virtual OBB folder")
                out = File(dest, name)
                val ins = a.contentResolver.openInputStream(uri)
                    ?: throw IOException("Cannot read $name")
                var copied = 0L
                var last = -1
                ins.use { i ->
                    FileOutputStream(out).use { o ->
                        val buf = ByteArray(256 * 1024)
                        while (true) {
                            val n = i.read(buf)
                            if (n < 0) break
                            o.write(buf, 0, n)
                            copied += n
                            val p = if (size > 0) ((copied * 100L) / size).toInt().coerceIn(0, 100) else 0
                            if (p != last) {
                                last = p
                                a.runOnUiThread {
                                    if (pd.isShowing) {
                                        pd.progress = p
                                        pd.setMessage("Copying OBB... $p%")
                                    }
                                }
                            }
                        }
                    }
                }
                a.runOnUiThread {
                    if (pd.isShowing) pd.dismiss()
                    dlg(a).setTitle("Information")
                        .setMessage("OBB copied:\n" + name)
                        .setPositiveButton("OK", null)
                        .show()
                    pendingAfter?.invoke()
                }
            } catch (e: Exception) {
                Log.e("AbdiLoader", "Manual OBB copy failed", e)
                try { out?.delete() } catch (x: Exception) { }
                a.runOnUiThread {
                    if (pd.isShowing) pd.dismiss()
                    Toast.makeText(a, "OBB copy error: " + e.message, Toast.LENGTH_LONG).show()
                }
            }
        }.start()
    }
}
"""
open(p, "w").write(code)
print("OK ->", p)
