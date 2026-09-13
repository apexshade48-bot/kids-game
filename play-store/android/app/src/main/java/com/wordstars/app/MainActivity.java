package com.wordstars.app;

import android.annotation.SuppressLint;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.inputmethod.EditorInfo;
import android.util.Log;
import android.webkit.ConsoleMessage;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import android.app.Activity;

public class MainActivity extends Activity {
    private WebView webView;
    private LinearLayout setup;
    private EditText urlBox;
    private SharedPreferences prefs;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        WebView.setWebContentsDebuggingEnabled(true);

        prefs = getSharedPreferences("wordstars", MODE_PRIVATE);
        String saved = prefs.getString("url", getString(R.string.game_url));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFFC4B5FD);

        setup = new LinearLayout(this);
        setup.setOrientation(LinearLayout.VERTICAL);
        setup.setPadding(40, 80, 40, 40);
        TextView title = new TextView(this);
        title.setText("Word Stars tester");
        title.setTextSize(22);
        title.setPadding(0, 0, 0, 24);
        TextView hint = new TextView(this);
        hint.setText("Type the PC address (same Wi-Fi). Example: http://192.168.100.27:5000");
        hint.setPadding(0, 0, 0, 16);
        urlBox = new EditText(this);
        urlBox.setText(saved);
        urlBox.setSingleLine(true);
        urlBox.setImeOptions(EditorInfo.IME_ACTION_GO);
        Button go = new Button(this);
        go.setText("Open game");
        setup.addView(title);
        setup.addView(hint);
        setup.addView(urlBox);
        setup.addView(go);

        webView = new WebView(this);
        webView.setLayoutParams(new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.MATCH_PARENT,
                1f
        ));
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setAllowFileAccess(false);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setTextZoom(100);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    webView.setVisibility(android.view.View.GONE);
                    setup.setVisibility(android.view.View.VISIBLE);
                    Toast.makeText(MainActivity.this,
                            "Cannot reach the game. Same Wi-Fi? Is python app.py running?",
                            Toast.LENGTH_LONG).show();
                }
            }
        });
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(PermissionRequest request) {
                request.grant(request.getResources());
            }

            @Override
            public boolean onConsoleMessage(ConsoleMessage cm) {
                Log.d("WordStarsWeb", cm.message() + " -- " + cm.sourceId() + ":" + cm.lineNumber());
                return true;
            }
        });

        go.setOnClickListener(v -> openGame());
        urlBox.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_GO
                    || (event != null && event.getKeyCode() == KeyEvent.KEYCODE_ENTER)) {
                openGame();
                return true;
            }
            return false;
        });

        root.addView(setup);
        root.addView(webView);
        webView.setVisibility(android.view.View.GONE);
        setContentView(root);

        openGame();
    }

    private void openGame() {
        String url = urlBox.getText().toString().trim();
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            url = "http://" + url;
        }
        if (url.endsWith("/")) {
            url = url.substring(0, url.length() - 1);
        }
        prefs.edit().putString("url", url).apply();
        setup.setVisibility(android.view.View.GONE);
        webView.setVisibility(android.view.View.VISIBLE);
        webView.loadUrl(url);
    }

    @Override
    public void onBackPressed() {
        if (webView.getVisibility() == android.view.View.VISIBLE && webView.canGoBack()) {
            webView.goBack();
        } else if (webView.getVisibility() == android.view.View.VISIBLE) {
            webView.setVisibility(android.view.View.GONE);
            setup.setVisibility(android.view.View.VISIBLE);
        } else {
            super.onBackPressed();
        }
    }
}
