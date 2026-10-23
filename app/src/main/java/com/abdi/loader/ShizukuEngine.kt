package com.abdi.loader

import android.content.pm.PackageManager
import android.os.Handler
import android.os.Looper
import rikka.shizuku.Shizuku

object ShizukuEngine {
    var isConnected = false
        private set
    private val handler = Handler(Looper.getMainLooper())

    private val permissionListener = Shizuku.OnRequestPermissionResultListener { requestCode, grantResult ->
        if (requestCode == 1001) {
            isConnected = grantResult == PackageManager.PERMISSION_GRANTED
        }
    }

    private val binderListener = Shizuku.OnBinderReceivedListener {
        checkStatus()
    }

    fun init() {
        try {
            Shizuku.addRequestPermissionResultListener(permissionListener)
            Shizuku.addBinderReceivedListener(binderListener)
            checkStatus()
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun checkStatus(): Boolean {
        if (Shizuku.isPreV11() || Shizuku.getVersion() < 11) return false
        isConnected = Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
        return isConnected
    }

    fun requestPermission() {
        if (!checkStatus()) {
            try {
                Shizuku.requestPermission(1001)
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
}
