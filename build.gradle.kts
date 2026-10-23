plugins {
    id("com.android.application") version "8.13.2" apply false
    id("com.android.library") version "8.13.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.23" apply false
}

extra["compileSdkVersion"] = 35
extra["targetSdkVersion"] = 28
extra["minSdk"] = 21
extra["versionCode"] = 1
extra["versionName"] = "1.0"
extra["xVersion"] = "1.1.0"
extra["hiddenApiBypass"] = "4.3"
