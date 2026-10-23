import re, shutil, subprocess

P = "app/src/main/java/com/abdi/loader/MainActivity.kt"

try:
    src = subprocess.check_output(["git", "show", "b59fb2f:" + P]).decode("utf-8")
except Exception:
    print("❌ Nooca nadiifka ah lama helin (b59fb2f). Waan joogsaday.")
    raise SystemExit

shutil.copy(P, P + ".bak_current")
print("✅ Faylka hadda jira waa la keydiyay: MainActivity.kt.bak_current")

NEW = r'''    private val ui = Handler(Looper.getMainLooper())
    private var ticker: Runnable? = null
    private var toastView: View? = null

    private fun stopTicker() {
        ticker?.let { ui.removeCallbacks(it) }
        ticker = null
    }

    private fun tint(c: Int) = Color.argb(44, Color.red(c), Color.green(c), Color.blue(c))

    private fun toast(msg: String, color: Int) {
        val deco = window.decorView as ViewGroup
        toastView?.let { deco.removeView(it) }
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            background = bg(Color.parseColor("#F01C1C1E"), 24, Color.parseColor("#3A3A3C"))
            setPadding(dp(16), dp(12), dp(20), dp(12))
            elevation = dp(8).toFloat()
        }
        val dot = View(this).apply {
            background = GradientDrawable().apply { shape = GradientDrawable.OVAL; setColor(color) }
        }
        row.addView(dot, LinearLayout.LayoutParams(dp(10), dp(10)))
        row.addView(TextView(this).apply {
            text = msg
            textSize = 15f
            setTextColor(Color.WHITE)
            typeface = Typeface.DEFAULT_BOLD
            setPadding(dp(10), 0, 0, 0)
        })
        val lpT = FrameLayout.LayoutParams(WRAP, WRAP, Gravity.TOP or Gravity.CENTER_HORIZONTAL)
        lpT.topMargin = dp(52)
        deco.addView(row, lpT)
        toastView = row
        row.alpha = 0f
        row.translationY = -dp(40).toFloat()
        row.animate().alpha(1f).translationY(0f).setDuration(320).start()
        row.postDelayed({
            row.animate().alpha(0f).translationY(-dp(30).toFloat()).setDuration(280).withEndAction {
                (row.parent as? ViewGroup)?.removeView(row)
                if (toastView === row) toastView = null
            }.start()
        }, 2400)
    }

    private fun showDashboard(r: JSONObject) {
        val games = r.optJSONArray("games")
        val expIso: String? = if (r.isNull("expires_at")) null else r.optString("expires_at")
        val expMs: Long? = if (expIso != null) parseMs(expIso) else null
        val n = games?.length() ?: 0

        val col = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(22), dp(48), dp(22), dp(40))
        }
        val head = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        head.addView(TextView(this).apply {
            text = "Games"
            textSize = 34f
            setTextColor(Color.WHITE)
            typeface = Typeface.DEFAULT_BOLD
        }, LinearLayout.LayoutParams(0, WRAP, 1f))
        head.addView(TextView(this).apply {
            text = "Logout"
            textSize = 16f
            setTextColor(BLUE)
            setPadding(dp(12), dp(8), dp(2), dp(8))
            setOnClickListener {
                prefs().edit().remove("key").apply()
                curKey = ""
                showLogin("", "")
            }
        })
        col.addView(head)

        val card = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                intArrayOf(Color.parseColor("#26262A"), Color.parseColor("#151517"))
            ).apply {
                cornerRadius = dp(26).toFloat()
                setStroke(dp(1), Color.parseColor("#34343A"))
            }
            setPadding(dp(22), dp(20), dp(22), dp(22))
        }
        val dot = View(this)
        val pill = TextView(this).apply {
            textSize = 12f
            typeface = Typeface.DEFAULT_BOLD
            setPadding(dp(10), dp(4), dp(10), dp(4))
        }
        val big = TextView(this).apply {
            textSize = 38f
            setTextColor(Color.WHITE)
            typeface = Typeface.DEFAULT_BOLD
            setPadding(0, dp(12), 0, 0)
        }
        val sub = TextView(this).apply {
            textSize = 14f
            setTextColor(MUTED)
            setPadding(0, dp(2), 0, 0)
        }
        val topRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        topRow.addView(dot, LinearLayout.LayoutParams(dp(8), dp(8)))
        topRow.addView(TextView(this).apply {
            text = "LICENSE"
            textSize = 12f
            letterSpacing = 0.12f
            setTextColor(MUTED)
            setPadding(dp(8), 0, 0, 0)
        }, LinearLayout.LayoutParams(0, WRAP, 1f))
        topRow.addView(pill)
        card.addView(topRow)
        card.addView(big)
        card.addView(sub)
        col.addView(card, lp(MATCH, WRAP, top = 18, bottom = 26))

        fun setStatus(c: Int, label: String) {
            dot.background = GradientDrawable().apply { shape = GradientDrawable.OVAL; setColor(c) }
            pill.text = label
            pill.setTextColor(c)
            pill.background = bg(tint(c), 12)
        }

        fun paint(): Boolean {
            if (expMs == null) {
                big.text = "Lifetime"
                sub.text = "Never expires"
                setStatus(GREEN, "Active")
                return true
            }
            val left = expMs - System.currentTimeMillis()
            val day = 86400000L
            val exp = SimpleDateFormat("MMM d, yyyy", Locale.ENGLISH).format(Date(expMs))
            if (left <= 0L) {
                big.text = "Expired"
                sub.text = "Ended $exp"
                setStatus(RED, "Expired")
                return false
            }
            if (left >= day) {
                val days = (left + day - 1) / day
                big.text = if (days == 1L) "1 day" else "$days days"
                sub.text = "Expires $exp"
                setStatus(if (days <= 3L) RED else if (days <= 7L) ORANGE else GREEN, "Active")
            } else {
                val h = left / 3600000L
                val m = (left / 60000L) % 60L
                val s = (left / 1000L) % 60L
                big.text = "${h}h ${m}m ${s}s"
                sub.text = "Expires $exp"
                setStatus(RED, "Ending soon")
            }
            return true
        }

        col.addView(TextView(this).apply {
            text = "YOUR GAMES"
            textSize = 12f
            letterSpacing = 0.12f
            setTextColor(MUTED)
            setPadding(dp(4), 0, 0, dp(10))
        })

        if (n == 0) {
            col.addView(TextView(this).apply {
                text = "No games available yet"
                textSize = 16f
                setTextColor(MUTED)
                gravity = Gravity.CENTER
                setPadding(0, dp(40), 0, dp(40))
            })
        }
        for (i in 0 until n) {
            val g = games!!.getJSONObject(i)
            val name = g.optString("name")
            val pkg = g.optString("package")
            val launch = packageManager.getLaunchIntentForPackage(pkg)

            val row = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                background = bg(CARD, 22)
                setPadding(dp(14), dp(14), dp(14), dp(14))
            }
            val icon: View = if (launch != null) {
                ImageView(this).apply {
                    scaleType = ImageView.ScaleType.FIT_CENTER
                    try { setImageDrawable(packageManager.getApplicationIcon(pkg)) } catch (e: Exception) { }
                }
            } else {
                TextView(this).apply {
                    text = name.take(2).uppercase()
                    textSize = 18f
                    setTextColor(MUTED)
                    typeface = Typeface.DEFAULT_BOLD
                    gravity = Gravity.CENTER
                    background = GradientDrawable(
                        GradientDrawable.Orientation.TL_BR,
                        intArrayOf(Color.parseColor("#3A3A3C"), Color.parseColor("#232325"))
                    )
                }
            }
            round(icon, 14)
            row.addView(icon, LinearLayout.LayoutParams(dp(54), dp(54)))

            val info = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(dp(14), 0, dp(8), 0)
            }
            info.addView(TextView(this).apply {
                text = name
                textSize = 16f
                setTextColor(Color.WHITE)
                typeface = Typeface.DEFAULT_BOLD
            })
            info.addView(TextView(this).apply {
                text = if (launch != null) "Installed" else "Not installed"
                textSize = 13f
                setTextColor(if (launch != null) GREEN else MUTED)
                setPadding(0, dp(3), 0, 0)
            })
            row.addView(info, LinearLayout.LayoutParams(0, WRAP, 1f))

            val go = Button(this).apply {
                text = "Open"
                setAllCaps(false)
                textSize = 15f
                setTextColor(Color.WHITE)
                typeface = Typeface.DEFAULT_BOLD
                stateListAnimator = null
                background = bg(if (launch != null) BLUE else Color.parseColor("#2C2C2E"), 22)
                isEnabled = launch != null
                setOnClickListener {
                    try {
                        startActivity(launch)
                        toast("Opening $name", BLUE)
                    } catch (e: Exception) {
                        toast("Could not open $name", RED)
                    }
                }
            }
            row.addView(go, LinearLayout.LayoutParams(dp(80), dp(42)))

            row.alpha = 0f
            row.translationY = dp(14).toFloat()
            row.animate().alpha(1f).translationY(0f).setStartDelay(i * 70L).setDuration(380).start()
            col.addView(row, lp(MATCH, WRAP, bottom = 12))
        }

        col.addView(TextView(this).apply {
            text = "Refresh"
            textSize = 15f
            setTextColor(BLUE)
            gravity = Gravity.CENTER
            setPadding(0, dp(18), 0, dp(18))
            setOnClickListener { showLoading(); verify(curKey) }
        })
        val sv = ScrollView(this).apply {
            setBackgroundColor(Color.BLACK)
            isFillViewport = true
            addView(col)
        }

        paint()
        show(sv)
        if (expMs != null) {
            val tick = object : Runnable {
                override fun run() {
                    if (!paint()) {
                        toast("License expired", RED)
                        ticker = null
                        ui.postDelayed({ if (curKey.isNotEmpty()) verify(curKey) }, 1500)
                        return
                    }
                    val left = expMs - System.currentTimeMillis()
                    ui.postDelayed(this, if (left < 86400000L) 1000L else 30000L)
                }
            }
            ticker = tick
            ui.postDelayed(tick, 1000L)
        }
        toast("License verified \u00b7 $n games", GREEN)
    }

'''

if "import android.os.Handler" not in src:
    src = src.replace("import android.os.Bundle", "import android.os.Bundle\nimport android.os.Handler\nimport android.os.Looper", 1)

old_show = "    private fun show(v: View) {\n        setContentView(v)"
if old_show not in src:
    print("❌ show() lama helin, waan joogsaday")
    raise SystemExit
src = src.replace(old_show, "    private fun show(v: View) {\n        stopTicker()\n        setContentView(v)", 1)

src, cnt = re.subn(r'    private fun showDashboard\(.*?(?=    private fun errText\()', lambda m: NEW, src, count=1, flags=re.S)
if cnt != 1:
    print("❌ showDashboard lama helin, waan joogsaday")
    raise SystemExit

with open(P, "w", encoding="utf-8") as f:
    f.write(src)
print("✅ Dashboard cusub (toast + license card + games) waa la qoray")
