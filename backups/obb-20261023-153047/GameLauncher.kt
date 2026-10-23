package com.abdi.loader

import android.app.Activity
import android.widget.Toast
import android.util.Log
import top.niunaijun.blackbox.BlackBoxCore

object GameLauncher {
    fun launch(activity: Activity, pkg: String, validate: () -> String? = { null }) {
        val error = validate()
        if (error != null) {
            Toast.makeText(activity, error, Toast.LENGTH_LONG).show()
            return
        }

        Toast.makeText(activity, "Preparing virtual game...", Toast.LENGTH_SHORT).show()

        Thread {
            try {
                val core = BlackBoxCore.get()
                val userId = 0

                if (!core.isInstalled(pkg, userId)) {
                    val result = core.installPackageAsUser(pkg, userId)
                    if (!core.isInstalled(pkg, userId)) {
                        activity.runOnUiThread {
                            Toast.makeText(
                                activity,
                                "Virtual install failed: $result",
                                Toast.LENGTH_LONG
                            ).show()
                        }
                        return@Thread
                    }
                }

                val launched = core.launchApk(pkg, userId)
                activity.runOnUiThread {
                    if (!launched) {
                        Toast.makeText(
                            activity,
                            "Virtual launch failed. Check engine setup.",
                            Toast.LENGTH_LONG
                        ).show()
                    }
                }
            } catch (e: Exception) {
                activity.runOnUiThread {
                    Toast.makeText(
                        activity,
                        "Virtual engine error: ${e.message}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
        }.start()
    }
}
