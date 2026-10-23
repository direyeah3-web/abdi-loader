import os, glob, shutil
R = os.path.expanduser("~/abdi-loader")
def w(rel, txt):
    p = os.path.join(R, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p) and not os.path.exists(p + ".bak"):
        shutil.copy(p, p + ".bak")
    open(p, "w").write(txt)

w("build.gradle.kts", '''plugins {
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
''')

w("app/build.gradle.kts", '''plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.abdi.loader"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.abdi.loader"
        minSdk = 24
        targetSdk = 28
        versionCode = 1
        versionName = "1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }
    kotlinOptions {
        jvmTarget = "21"
    }
    packaging {
        jniLibs { useLegacyPackaging = true }
    }
}

dependencies {
    implementation("androidx.documentfile:documentfile:1.0.1")
    implementation(project(":Bcore"))
}
''')

ymls = glob.glob(os.path.join(R, ".github/workflows/*.yml"))
wf = os.path.relpath(ymls[0], R) if ymls else ".github/workflows/build.yml"
w(wf, '''name: Build APK
on:
  push:
    branches: [main, new-engine]
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: 21
      - name: Install NDK 29
        run: |
          yes | $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --licenses > /dev/null || true
          $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager "ndk;29.0.13846066" "platforms;android-35"
      - uses: gradle/actions/setup-gradle@v4
        with:
          gradle-version: 8.14.5
      - run: gradle assembleDebug --no-daemon
      - uses: actions/upload-artifact@v4
        with:
          name: abdi-loader-apk
          path: app/build/outputs/apk/debug/app-debug.apk
''')

gp = os.path.join(R, "gradle.properties")
cur = open(gp).read() if os.path.exists(gp) else ""
if cur:
    shutil.copy(gp, gp + ".bak")
keys = {l.split("=")[0].strip() for l in cur.splitlines() if "=" in l}
up = os.path.expanduser("~/NewBlackbox/gradle.properties")
add = []
if os.path.exists(up):
    for l in open(up).read().splitlines():
        if "=" in l and not l.strip().startswith("#") and l.split("=")[0].strip() not in keys:
            add.append(l)
            keys.add(l.split("=")[0].strip())
for k, v in [("android.useAndroidX", "true"), ("org.gradle.jvmargs", "-Xmx4g")]:
    if k not in keys:
        add.append(k + "=" + v)
open(gp, "w").write(cur.rstrip("\n") + "\n" + "\n".join(add) + "\n")
print("OK:", wf)
