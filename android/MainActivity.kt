package com.example.dndtoolbox

import android.content.Intent
import android.os.Bundle
import android.os.Message
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView
    private val homeUrl = "http://127.0.0.1:8000/"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 0. Go edge-to-edge explicitly so the system reliably dispatches window
        //    insets to our view (we pad for them below). Required on Android 15+.
        WindowCompat.setDecorFitsSystemWindows(window, false)

        // 1. Start Python (once) and kick off the Flask server on a background thread.
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        Python.getInstance()
            .getModule("android_main")
            .callAttr("start", filesDir.absolutePath)

        // 2. Full-screen WebView pointed at the local server.
        web = WebView(this)
        web.keepScreenOn = true
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.setSupportMultipleWindows(true)
        web.settings.javaScriptCanOpenWindowsAutomatically = true

        // target="_blank" / window.open (footer credit link, 5e.tools links) → open in
        // the system browser instead of being silently blocked by the WebView.
        web.webChromeClient = object : WebChromeClient() {
            override fun onCreateWindow(view: WebView, isDialog: Boolean, isUserGesture: Boolean, resultMsg: Message): Boolean {
                val tmp = WebView(view.context)
                tmp.webViewClient = object : WebViewClient() {
                    override fun shouldOverrideUrlLoading(v: WebView, request: WebResourceRequest): Boolean {
                        startActivity(Intent(Intent.ACTION_VIEW, request.url))
                        return true
                    }
                }
                (resultMsg.obj as WebView.WebViewTransport).webView = tmp
                resultMsg.sendToTarget()
                return true
            }
        }

        web.webViewClient = object : WebViewClient() {
            // Keep app pages in the WebView; send external links (5e.tools) to the browser.
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url.toString()
                if (url.contains("127.0.0.1")) return false
                startActivity(Intent(Intent.ACTION_VIEW, request.url))
                return true
            }

            // The server may still be starting on first launch — retry the home page.
            override fun onReceivedError(view: WebView, request: WebResourceRequest, error: WebResourceError) {
                if (request.isForMainFrame) {
                    view.postDelayed({ view.loadUrl(homeUrl) }, 500)
                }
            }
        }

        setContentView(web)

        // Pad the WebView clear of the status/navigation bars so the top toolbar is
        // never under the clock/battery overlay. The inset-listener dispatch is
        // unreliable on some OEM skins (HyperOS), so we read the insets directly on
        // every layout pass (rotation included) and fall back to the resource-defined
        // status-bar height if the system reports zero.
        web.viewTreeObserver.addOnGlobalLayoutListener { applyBarPadding() }
        applyBarPadding()

        // 3. Give the server a moment to bind, then load the UI (retries on error above).
        web.postDelayed({ web.loadUrl(homeUrl) }, 800)
    }

    // Pad the WebView by the system bars; guarded so it doesn't loop on re-layout.
    private fun applyBarPadding() {
        val sys = ViewCompat.getRootWindowInsets(web)
            ?.getInsets(WindowInsetsCompat.Type.systemBars())
        var top = sys?.top ?: 0
        val left = sys?.left ?: 0
        val right = sys?.right ?: 0
        val bottom = sys?.bottom ?: 0
        if (top == 0) {
            // OEM skin didn't report a status-bar inset — use the system resource.
            val resId = resources.getIdentifier("status_bar_height", "dimen", "android")
            if (resId > 0) top = resources.getDimensionPixelSize(resId)
        }
        if (web.paddingTop != top || web.paddingLeft != left ||
            web.paddingRight != right || web.paddingBottom != bottom) {
            web.setPadding(left, top, right, bottom)
        }
    }

    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }
}
