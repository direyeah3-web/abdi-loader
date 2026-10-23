import os

FILES = {}

FILES[".github/workflows/build.yml"] = r'''name: Build APK
on:
  push:
    branches: [main]
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: 17
      - uses: gradle/actions/setup-gradle@v4
        with:
          gradle-version: 8.7
      - run: gradle assembleDebug --no-daemon
      - uses: actions/upload-artifact@v4
        with:
          name: abdi-loader-apk
          path: app/build/outputs/apk/debug/app-debug.apk
'''

FILES["settings.gradle.kts"] = r'''pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "AbdiLoader"
include(":app")
'''

FILES["build.gradle.kts"] = r'''plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.24" apply false
}
'''

FILES["gradle.properties"] = r'''org.gradle.jvmargs=-Xmx2g
android.useAndroidX=true
android.nonTransitiveRClass=true
'''

FILES["app/build.gradle.kts"] = r'''plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "com.abdi.loader"
    compileSdk = 34
    defaultConfig {
        applicationId = "com.abdi.loader"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}
'''

FILES["app/src/main/AndroidManifest.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET"/>
    <application
        android:label="Abdi Loader"
        android:allowBackup="false"
        android:theme="@android:style/Theme.DeviceDefault.NoActionBar">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>
'''

FILES["app/src/main/java/com/abdi/loader/MainActivity.kt"] = r'''package com.abdi.loader

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.provider.Settings
import android.text.InputType
import android.view.Gravity
import android.widget.*
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : Activity() {
    private val base = "https://qnbiqgntqhzromwnmyth.supabase.co"
    private val anon = "sb_publishable_-jVYtd4Psza1wjuBe8g3CQ_kjxRB4lL"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val pad = (24 * resources.displayMetrics.density).toInt()
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.BLACK)
            setPadding(pad, pad, pad, pad)
        }
        val title = TextView(this).apply {
            text = "Abdi Loader"
            textSize = 30f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
        }
        val input = EditText(this).apply {
            hint = "License key"
            setHintTextColor(Color.GRAY)
            setTextColor(Color.WHITE)
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS
            setText(getSharedPreferences("a", MODE_PRIVATE).getString("key", ""))
        }
        val btn = Button(this).apply { text = "Hubi key-ga" }
        val status = TextView(this).apply {
            textSize = 16f
            setTextColor(Color.LTGRAY)
            gravity = Gravity.CENTER
            setPadding(0, pad, 0, 0)
        }
        root.addView(title)
        root.addView(input)
        root.addView(btn)
        root.addView(status)
        setContentView(root)

        val device = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown-device"
        btn.setOnClickListener {
            val key = input.text.toString().trim()
            status.text = "Waa la hubinayaa..."
            btn.isEnabled = false
            Thread {
                val msg = try { check(key, device) } catch (e: Exception) { "Khalad network: isku day mar kale" }
                runOnUiThread {
                    status.text = msg
                    btn.isEnabled = true
                }
            }.start()
        }
    }

    private fun check(key: String, device: String): String {
        val c = URL("$base/rest/v1/rpc/validate_key").openConnection() as HttpURLConnection
        c.requestMethod = "POST"
        c.connectTimeout = 10000
        c.readTimeout = 10000
        c.setRequestProperty("apikey", anon)
        c.setRequestProperty("Content-Type", "application/json")
        c.doOutput = true
        val body = JSONObject().put("p_key", key).put("p_device", device).toString()
        c.outputStream.use { it.write(body.toByteArray()) }
        val stream = if (c.responseCode in 200..299) c.inputStream else c.errorStream
        val text = stream.bufferedReader().use { it.readText() }
        val j = JSONObject(text)
        if (j.optBoolean("ok")) {
            getSharedPreferences("a", MODE_PRIVATE).edit().putString("key", key).apply()
            return "Key waa sax"
        }
        return when (j.optString("error")) {
            "invalid_key" -> "Key khalad ah"
            "inactive" -> "Key-gan waa la damiyay"
            "expired" -> "Key-gan wuu dhacay"
            "device_limit" -> "Xadka aaladaha waa buuxaa"
            "banned" -> "Akoonkan waa la xiray"
            else -> "Khalad aan la aqoon"
        }
    }
}
'''

FILES[".gitignore"] = ".gradle/\nbuild/\nlocal.properties\n*.keystore\n*.jks\n"

for path, content in FILES.items():
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅", path)
