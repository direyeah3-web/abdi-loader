package com.abdi.loader

import android.content.pm.PackageManager
import rikka.shizuku.Shizuku

object ShizukuEngine {
    var isConnected = false
        private set

    fun checkStatus(): Boolean {
        if (Shizuku.isPreV11() || Shizuku.getVersion() < 11) return false
        isConnected = Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
        return isConnected
    }

    fun requestPermission(requestCode: Int = 1001) {
        if (!checkStatus()) {
            try {
                Shizuku.requestPermission(requestCode)
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
}
