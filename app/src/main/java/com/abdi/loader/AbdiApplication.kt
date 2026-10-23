package com.abdi.loader

import android.app.Application
import android.content.Context
import android.util.Log
import top.niunaijun.blackbox.BlackBoxCore
import top.niunaijun.blackbox.app.configuration.ClientConfiguration

class AbdiApplication : Application() {
    override fun attachBaseContext(base: Context) {
        super.attachBaseContext(base)
        BlackBoxCore.get().doAttachBaseContext(
            base,
            object : ClientConfiguration() {
                override fun getHostPackageName(): String = base.packageName
            }
        )
        Log.i("AbdiLoader", "BlackBoxCore attached: ${base.packageName}")
    }

    override fun onCreate() {
        super.onCreate()
        BlackBoxCore.get().doCreate()
        Log.i("AbdiLoader", "BlackBoxCore created")
    }
}
