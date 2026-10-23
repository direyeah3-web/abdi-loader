from pathlib import Path
import re

root = Path(".")
main = root / "app/src/main/java/com/abdi/loader/MainActivity.kt"
launcher = root / "app/src/main/java/com/abdi/loader/GameLauncher.kt"
gradle = root / "app/build.gradle.kts"

s = main.read_text()

if "private var pendingGamePackage" not in s:
    s = s.replace(
        '    private var curKey = ""',
        '''    private var curKey = ""
    private var pendingGamePackage: String? = null
    private val obbPickerRequest = 7401

    private fun openGame(pkg: String) {
        val saved = prefs().getString("obb_tree_uri", null)
        if (!saved.isNullOrBlank()) {
            GameLauncher.launch(this, pkg, Uri.parse(saved))
            return
        }
        pendingGamePackage = pkg
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE).apply {
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
        }
        try {
            startActivityForResult(intent, obbPickerRequest)
        } catch (e: Exception) {
            pendingGamePackage = null
            Toast.makeText(this, "Cannot open folder picker: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    @Deprecated("Uses the system folder picker result")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != obbPickerRequest) return

        val pkg = pendingGamePackage
        pendingGamePackage = null
        val uri = if (resultCode == RESULT_OK) data?.data else null

        if (pkg == null) return
        if (uri == null) {
            Toast.makeText(this, "Folder selection cancelled", Toast.LENGTH_SHORT).show()
            return
        }

        try {
            val flags = data?.flags ?: 0
            contentResolver.takePersistableUriPermission(
                uri,
                flags and (Intent.FLAG_GRANT_READ_URI_PERMISSION or
                    Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            )
            prefs().edit().putString("obb_tree_uri", uri.toString()).apply()
            GameLauncher.launch(this, pkg, uri)
        } catch (e: Exception) {
            Toast.makeText(this, "Folder permission failed: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }'''
    )

s = s.replace(
    'GameLauncher.launch(this@MainActivity, pkg)',
    'openGame(pkg)'
)
if 'import android.net.Uri' not in s:
    s = s.replace('import android.content.Context', 'import android.content.Context\nimport android.net.Uri')
if 'import android.widget.Toast' not in s:
    s = s.replace('import android.widget.*', 'import android.widget.*')
main.write_text(s)

launcher.write_text(r'''package com.abdi.loader

import android.app.Activity
import android.app.ProgressDialog
import android.content.Intent
import android.net.Uri
import android.util.Log
import android.widget.Toast
import androidx.documentfile.provider.DocumentFile
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import top.niunaijun.blackbox.BlackBoxCore
import top.niunaijun.blackbox.core.env.BEnvironment

object GameLauncher {
    fun launch(activity: Activity, pkg: String, treeUri: Uri, validate: () -> String? = { null }) {
        val error = validate()
        if (error != null) {
            Toast.makeText(activity, error, Toast.LENGTH_LONG).show()
            return
        }

        val dialog = ProgressDialog(activity).apply {
            setTitle("Abdi Loader")
            setMessage("Finding PUBG OBB files...")
            setProgressStyle(ProgressDialog.STYLE_HORIZONTAL)
            max = 100
            progress = 0
            setCancelable(false)
            show()
        }

        Thread {
            try {
                val tree = DocumentFile.fromTreeUri(activity, treeUri)
                    ?: throw IOException("Cannot access selected folder")

                fun findPackageFolder(dir: DocumentFile): DocumentFile? {
                    if (dir.name == pkg && dir.isDirectory) return dir
                    for (child in dir.listFiles()) {
                        if (child.isDirectory) {
                            val found = findPackageFolder(child)
                            if (found != null) return found
                        }
                    }
                    return null
                }

                fun collectObb(dir: DocumentFile, out: MutableList<DocumentFile>) {
                    for (child in dir.listFiles()) {
                        if (child.isDirectory) collectObb(child, out)
                        else if (child.isFile && child.name?.endsWith(".obb", true) == true) {
                            out.add(child)
                        }
                    }
                }

                val packageFolder = if (tree.name == pkg) tree else findPackageFolder(tree)
                val files = mutableListOf<DocumentFile>()
                collectObb(packageFolder ?: tree, files)

                val destination = BEnvironment.getExternalObbDir(pkg, 0)
                if (files.isEmpty()) {
                    val existing = destination.exists() &&
                        destination.walkTopDown().any { it.isFile && it.extension.equals("obb", true) }
                    if (!existing) {
                        throw IOException(
                            "No .obb files found. Select the folder containing " +
                            "Android/obb/$pkg, or select the $pkg folder itself."
                        )
                    }
                } else {
                    if (!destination.exists() && !destination.mkdirs()) {
                        throw IOException("Cannot create virtual OBB folder")
                    }

                    val total = files.sumOf { it.length() }.coerceAtLeast(1L)
                    var copied = 0L
                    var lastPercent = -1

                    for (doc in files) {
                        val name = doc.name ?: continue
                        val output = File(destination, name)
                        val length = doc.length()

                        if (output.exists() && output.length() == length && length > 0L) {
                            copied += length
                            continue
                        }

                        val input = activity.contentResolver.openInputStream(doc.uri)
                            ?: throw IOException("Cannot read OBB file: $name")
                        input.use { ins ->
                            FileOutputStream(output).use { outs ->
                                val buffer = ByteArray(256 * 1024)
                                while (true) {
                                    val n = ins.read(buffer)
                                    if (n < 0) break
                                    outs.write(buffer, 0, n)
                                    copied += n
                                    val percent = ((copied * 100L) / total).toInt().coerceIn(0, 100)
                                    if (percent != lastPercent) {
                                        lastPercent = percent
                                        activity.runOnUiThread {
                                            if (dialog.isShowing) {
                                                dialog.progress = percent
                                                dialog.setMessage("Copying OBB... $percent%")
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                activity.runOnUiThread {
                    if (dialog.isShowing) dialog.setMessage("Starting virtual game...")
                }

                val core = BlackBoxCore.get()
                val userId = 0
                if (!core.isInstalled(pkg, userId)) {
                    val result = core.installPackageAsUser(pkg, userId)
                    if (!core.isInstalled(pkg, userId)) {
                        throw IOException("Virtual installation failed: $result")
                    }
                }

                if (!core.launchApk(pkg, userId)) {
                    throw IOException("Virtual engine could not launch $pkg")
                }

                activity.runOnUiThread {
                    if (dialog.isShowing) dialog.dismiss()
                    Toast.makeText(activity, "Launch started", Toast.LENGTH_LONG).show()
                }
            } catch (e: Exception) {
                Log.e("AbdiLoader", "OBB copy / virtual launch failed", e)
                activity.runOnUiThread {
                    if (dialog.isShowing) dialog.dismiss()
                    Toast.makeText(activity, "Loader error: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }
        }.start()
    }
}
''')

g = gradle.read_text()
if "androidx.documentfile:documentfile" not in g:
    match = re.search(r'dependencies\s*\{', g)
    if not match:
        raise SystemExit("Could not find dependencies { } in app/build.gradle.kts")
    pos = match.end()
    g = g[:pos] + '\n    implementation("androidx.documentfile:documentfile:1.0.1")' + g[pos:]
    gradle.write_text(g)

print("Patch applied.")
print("Open now asks you to select a folder and remembers the selection.")
