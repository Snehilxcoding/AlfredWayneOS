# test_window.py
import webview

webview.create_window(
    'Alfred',
    'dashboard_ui.html',
    fullscreen=True,
    frameless=True,
    background_color='#000000'
)
webview.start()