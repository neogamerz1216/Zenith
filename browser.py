import sys
import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtGui import QIcon, QColor, QFont, QPainter, QPen, QPixmap, QPainterPath

# ==========================================
# 1. BACKGROUND DATA WORKER
# ==========================================
class LiveDataWorker(QThread):
    data_ready = pyqtSignal(dict)

    def run(self):
        live_data = {
            "weather": {"temp": "--", "desc": "Loading..."},
            "news": []
        }
        
        try:
            weather_url = "https://api.open-meteo.com/v1/forecast?latitude=17.3850&longitude=78.4867&current_weather=true"
            req = urllib.request.Request(weather_url, headers={'User-Agent': 'Zenith/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                w_data = json.loads(response.read().decode())
                live_data["weather"]["temp"] = f"{w_data['current_weather']['temperature']}°C"
                live_data["weather"]["desc"] = "Clear" if w_data['current_weather']['weathercode'] == 0 else "Cloudy"
        except Exception:
            pass

        try:
            news_url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
            req = urllib.request.Request(news_url, headers={'User-Agent': 'Zenith/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                for item in root.findall('./channel/item')[:6]:
                    live_data["news"].append({
                        "title": item.find('title').text, 
                        "link": item.find('link').text
                    })
        except Exception:
            pass
            
        self.data_ready.emit(live_data)

# ==========================================
# 2. MAIN BROWSER APP
# ==========================================
class ZenithBrowser(QMainWindow):
    def __init__(self):
        super(ZenithBrowser, self).__init__()

        self.search_engine = "Google"
        self.is_dark_mode = True
        self.history_log = []
        
        self.live_news = []
        self.live_weather = {"temp": "--", "desc": "--"}

        self.apply_theme()

        # --- TABS ---
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        
        # --- SIDEBAR ---
        self.sidebar = QDockWidget("Activity History", self)
        self.sidebar.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.load_history_item)
        self.sidebar.setWidget(self.history_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)
        self.sidebar.hide() # Hidden by default for a clean look

        # --- LAYOUT ---
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self.nav_wrapper = QWidget()
        self.nav_wrapper.setObjectName("NavContainer")
        nav_layout = QHBoxLayout(self.nav_wrapper)
        nav_layout.setContentsMargins(10, 8, 10, 8)
        nav_layout.setSpacing(8)

        self.toggle_sidebar_btn = self.create_nav_button("Toggle history panel", self.toggle_sidebar)
        self.back_btn = self.create_nav_button("Go back", self.go_back)
        self.forward_btn = self.create_nav_button("Go forward", self.go_forward)
        self.reload_btn = self.create_nav_button("Reload page", self.reload_page)
        self.home_btn = self.create_nav_button("Go to start page", self.go_home)

        self.engine_selector = QComboBox()
        self.engine_selector.addItems(["Google", "DuckDuckGo", "Bing"])
        self.engine_selector.currentIndexChanged.connect(self.change_engine)
        self.engine_selector.setFixedWidth(110)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or enter web address")
        self.url_bar.returnPressed.connect(self.navigate_to_url)

        self.theme_btn = self.create_nav_button("Toggle theme", self.toggle_theme)

        self.add_tab_btn = self.create_nav_button("New tab", lambda: self.add_new_tab(), object_name="AccentBtn")
        self.set_toolbar_icons()

        nav_layout.addWidget(self.toggle_sidebar_btn)
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.forward_btn)
        nav_layout.addWidget(self.reload_btn)
        nav_layout.addWidget(self.home_btn)
        nav_layout.addWidget(self.engine_selector)
        nav_layout.addWidget(self.url_bar, 1)
        nav_layout.addWidget(self.theme_btn)
        nav_layout.addWidget(self.add_tab_btn)

        layout.addWidget(self.nav_wrapper)
        layout.addWidget(self.tabs)
        self.setCentralWidget(container)

        self.setWindowTitle("Zenith Browser")
        self.resize(1200, 800)
        self.add_new_tab(QUrl('about:home'), 'Start Page')

        # Start API Fetcher
        self.fetcher = LiveDataWorker()
        self.fetcher.data_ready.connect(self.update_live_data)
        self.fetcher.start()

    def create_nav_button(self, tooltip, callback, object_name="NavBtn"):
        btn = QToolButton()
        btn.setObjectName(object_name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setIconSize(QSize(18, 18))
        btn.setFixedSize(34, 34)
        btn.clicked.connect(callback)
        return btn

    def build_nav_icon(self, icon_name, accent=False):
        size = 22
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        stroke = QColor("#E5E7EB" if self.is_dark_mode else "#1F2937")
        if accent:
            stroke = QColor("#60A5FA" if self.is_dark_mode else "#2563EB")

        pen = QPen(
            stroke,
            2.0,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin
        )
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if icon_name == "menu":
            painter.drawLine(QPointF(5.0, 6.0), QPointF(17.0, 6.0))
            painter.drawLine(QPointF(5.0, 11.0), QPointF(17.0, 11.0))
            painter.drawLine(QPointF(5.0, 16.0), QPointF(17.0, 16.0))
        elif icon_name == "back":
            painter.drawLine(QPointF(14.8, 5.5), QPointF(8.5, 11.0))
            painter.drawLine(QPointF(8.5, 11.0), QPointF(14.8, 16.5))
            painter.drawLine(QPointF(9.5, 11.0), QPointF(18.0, 11.0))
        elif icon_name == "forward":
            painter.drawLine(QPointF(7.2, 5.5), QPointF(13.5, 11.0))
            painter.drawLine(QPointF(13.5, 11.0), QPointF(7.2, 16.5))
            painter.drawLine(QPointF(4.0, 11.0), QPointF(12.5, 11.0))
        elif icon_name == "reload":
            painter.drawArc(QRectF(5.0, 5.0, 12.0, 12.0), 35 * 16, 290 * 16)
            painter.drawLine(QPointF(15.8, 4.3), QPointF(18.2, 4.8))
            painter.drawLine(QPointF(15.8, 4.3), QPointF(15.2, 6.8))
        elif icon_name == "home":
            painter.drawLine(QPointF(4.5, 10.2), QPointF(11.0, 5.0))
            painter.drawLine(QPointF(11.0, 5.0), QPointF(17.5, 10.2))
            painter.drawRect(QRectF(6.5, 10.2, 9.0, 7.2))
            painter.drawLine(QPointF(10.8, 17.4), QPointF(10.8, 13.8))
        elif icon_name == "theme":
            if self.is_dark_mode:
                painter.drawEllipse(QPointF(11.0, 11.0), 3.1, 3.1)
                painter.drawLine(QPointF(11.0, 2.8), QPointF(11.0, 4.6))
                painter.drawLine(QPointF(11.0, 17.4), QPointF(11.0, 19.2))
                painter.drawLine(QPointF(2.8, 11.0), QPointF(4.6, 11.0))
                painter.drawLine(QPointF(17.4, 11.0), QPointF(19.2, 11.0))
                painter.drawLine(QPointF(5.0, 5.0), QPointF(6.3, 6.3))
                painter.drawLine(QPointF(15.7, 15.7), QPointF(17.0, 17.0))
                painter.drawLine(QPointF(5.0, 17.0), QPointF(6.3, 15.7))
                painter.drawLine(QPointF(15.7, 6.3), QPointF(17.0, 5.0))
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(stroke)
                moon = QPainterPath()
                moon.addEllipse(QRectF(5.0, 4.0, 12.0, 12.0))
                cutout = QPainterPath()
                cutout.addEllipse(QRectF(9.0, 3.6, 11.5, 12.0))
                painter.drawPath(moon.subtracted(cutout))
        elif icon_name == "add":
            painter.drawLine(QPointF(11.0, 5.0), QPointF(11.0, 17.0))
            painter.drawLine(QPointF(5.0, 11.0), QPointF(17.0, 11.0))

        painter.end()
        return QIcon(pixmap)

    def set_toolbar_icons(self):
        self.toggle_sidebar_btn.setIcon(self.build_nav_icon("menu"))
        self.back_btn.setIcon(self.build_nav_icon("back"))
        self.forward_btn.setIcon(self.build_nav_icon("forward"))
        self.reload_btn.setIcon(self.build_nav_icon("reload"))
        self.home_btn.setIcon(self.build_nav_icon("home"))
        self.theme_btn.setIcon(self.build_nav_icon("theme"))
        self.add_tab_btn.setIcon(self.build_nav_icon("add", accent=True))

    # ==========================================
    # 3. HTML HOMEPAGE (FIXED CSP ERROR)
    # ==========================================
    def update_live_data(self, data):
        self.live_weather = data["weather"]
        self.live_news = data["news"]
        if self.tabs.currentWidget() and self.url_bar.text() == "about:home":
            self.tabs.currentWidget().setHtml(self.get_home_html())

    def get_home_html(self):
        # Professional Colors
        bg_color = "#1E1E1E" if self.is_dark_mode else "#F9F9FB"
        text_color = "#FFFFFF" if self.is_dark_mode else "#1F2937"
        card_bg = "#2D2D30" if self.is_dark_mode else "#FFFFFF"
        border_color = "#3E3E42" if self.is_dark_mode else "#E5E7EB"
        accent_color = "#3B82F6"
        
        # CSP Fix: Determine the form action based on the selected engine
        if self.search_engine == "Google":
            action_url = "https://www.google.com/search"
        elif self.search_engine == "Bing":
            action_url = "https://www.bing.com/search"
        else:
            action_url = "https://duckduckgo.com/"

        news_html = ""
        if not self.live_news:
            news_html = f"<p style='color: {text_color}; opacity: 0.6;'>Fetching latest headlines...</p>"
        else:
            for item in self.live_news:
                news_html += f"""
                <a href="{item['link']}" class="news-card">
                    <div class="news-title">{item['title']}</div>
                </a>
                """

        # Notice the strict HTML form instead of inline JavaScript!
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ background: {bg_color}; color: {text_color}; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 40px; }}
                .top-bar {{ display: flex; justify-content: flex-end; margin-bottom: 60px; }}
                .weather-widget {{ background: {card_bg}; padding: 12px 20px; border-radius: 12px; border: 1px solid {border_color}; font-weight: 500; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
                
                .hero {{ text-align: center; margin-bottom: 60px; }}
                .logo {{ font-size: 48px; font-weight: 700; color: {accent_color}; margin-bottom: 10px; }}
                .greeting {{ font-size: 18px; opacity: 0.7; margin-bottom: 30px; }}
                
                .search-form {{ width: 100%; max-width: 600px; margin: 0 auto; }}
                .search-bar {{ width: 100%; padding: 16px 24px; border-radius: 24px; border: 1px solid {border_color}; background: {card_bg}; color: {text_color}; font-size: 16px; outline: none; transition: all 0.2s ease; box-sizing: border-box; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
                .search-bar:focus {{ border-color: {accent_color}; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2); }}
                
                .section-title {{ font-size: 18px; font-weight: 600; margin-bottom: 20px; }}
                .news-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; max-width: 1000px; margin: 0 auto; }}
                .news-card {{ background: {card_bg}; border-radius: 12px; padding: 20px; border: 1px solid {border_color}; transition: all 0.2s ease; text-decoration: none; color: {text_color}; display: block; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
                .news-card:hover {{ border-color: {accent_color}; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
                .news-title {{ font-size: 15px; font-weight: 500; line-height: 1.5; }}
            </style>
        </head>
        <body>
            <div class="top-bar">
                <div class="weather-widget">
                    📍 Hyderabad: {self.live_weather['temp']} ({self.live_weather['desc']})
                </div>
            </div>

            <div class="hero">
                <div class="logo">Zenith</div>
                <div class="greeting">Welcome back, Pavan</div>
                
                <form class="search-form" action="{action_url}" method="GET">
                    <input type="text" name="q" class="search-bar" placeholder="Search the web securely..." required autofocus autocomplete="off">
                </form>
            </div>

            <div style="max-width: 1000px; margin: 0 auto;">
                <div class="section-title">Top Stories</div>
                <div class="news-grid">
                    {news_html}
                </div>
            </div>
        </body>
        </html>
        """

    # ==========================================
    # 4. POLISHED UI THEMING
    # ==========================================
    def apply_theme(self):
        if self.is_dark_mode:
            self.setStyleSheet("""
                QMainWindow { background-color: #1E1E1E; }
                #NavContainer { background-color: #2D2D30; border-bottom: 1px solid #3E3E42; }
                QTabBar::tab { background: transparent; color: #A0A0A5; padding: 10px 18px; margin-top: 5px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-size: 13px; min-width: 140px; }
                QTabBar::tab:selected { background: #1E1E1E; color: #FFFFFF; font-weight: bold; border: 1px solid #3E3E42; border-bottom: none; }
                QTabBar::tab:hover:!selected { background: #3E3E42; color: #FFFFFF; }
                QLineEdit { background-color: #1E1E1E; border: 1px solid #3E3E42; border-radius: 16px; padding: 8px 16px; color: #FFFFFF; font-size: 13px; }
                QLineEdit:focus { border: 1px solid #3B82F6; }
                QToolButton { border: 1px solid transparent; border-radius: 17px; padding: 6px; background: transparent; }
                QToolButton:hover { background: #3E3E42; border: 1px solid #4B5563; }
                QToolButton:pressed { background: #4B5563; }
                QToolButton#AccentBtn { background: rgba(59, 130, 246, 0.16); border: 1px solid rgba(59, 130, 246, 0.35); }
                QToolButton#AccentBtn:hover { background: rgba(59, 130, 246, 0.28); border: 1px solid rgba(59, 130, 246, 0.55); }
                QComboBox { background-color: #1E1E1E; color: #FFFFFF; border-radius: 10px; padding: 6px 12px; border: 1px solid #3E3E42; }
                QDockWidget { color: #FFFFFF; font-weight: bold; titlebar-close-icon: url(''); titlebar-normal-icon: url(''); }
                QListWidget { background-color: #2D2D30; color: #A0A0A5; border: none; outline: none; padding: 10px; font-size: 13px; }
                QListWidget::item { padding: 8px; border-radius: 6px; }
                QListWidget::item:hover { background-color: #3E3E42; color: #FFFFFF; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #F9F9FB; }
                #NavContainer { background-color: #FFFFFF; border-bottom: 1px solid #E5E7EB; }
                QTabBar::tab { background: transparent; color: #6B7280; padding: 10px 18px; margin-top: 5px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-size: 13px; min-width: 140px; }
                QTabBar::tab:selected { background: #F9F9FB; color: #111827; font-weight: bold; border: 1px solid #E5E7EB; border-bottom: none; }
                QTabBar::tab:hover:!selected { background: #F3F4F6; color: #111827; }
                QLineEdit { background-color: #F9F9FB; border: 1px solid #E5E7EB; border-radius: 16px; padding: 8px 16px; color: #111827; font-size: 13px; }
                QLineEdit:focus { border: 1px solid #3B82F6; }
                QToolButton { border: 1px solid transparent; border-radius: 17px; padding: 6px; background: transparent; }
                QToolButton:hover { background: #F3F4F6; border: 1px solid #D1D5DB; }
                QToolButton:pressed { background: #E5E7EB; }
                QToolButton#AccentBtn { background: rgba(37, 99, 235, 0.12); border: 1px solid rgba(37, 99, 235, 0.28); }
                QToolButton#AccentBtn:hover { background: rgba(37, 99, 235, 0.2); border: 1px solid rgba(37, 99, 235, 0.45); }
                QComboBox { background-color: #F9F9FB; color: #111827; border-radius: 10px; padding: 6px 12px; border: 1px solid #E5E7EB; }
                QDockWidget { color: #111827; font-weight: bold; }
                QListWidget { background-color: #FFFFFF; color: #4B5563; border: none; outline: none; padding: 10px; font-size: 13px; }
                QListWidget::item { padding: 8px; border-radius: 6px; }
                QListWidget::item:hover { background-color: #F3F4F6; color: #111827; }
            """)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        self.set_toolbar_icons()
        if self.url_bar.text() == "about:home":
            self.tabs.currentWidget().setHtml(self.get_home_html())

    def go_back(self):
        browser = self.tabs.currentWidget()
        if browser:
            browser.back()

    def go_forward(self):
        browser = self.tabs.currentWidget()
        if browser:
            browser.forward()

    def reload_page(self):
        browser = self.tabs.currentWidget()
        if browser:
            browser.reload()

    def go_home(self):
        browser = self.tabs.currentWidget()
        if browser:
            browser.setHtml(self.get_home_html())
            self.url_bar.setText("about:home")

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def change_engine(self):
        self.search_engine = self.engine_selector.currentText()
        if self.url_bar.text() == "about:home":
            self.tabs.currentWidget().setHtml(self.get_home_html())

    def log_history(self, title, url):
        if not url.startswith("data:text/html") and url != "about:blank":
            entry = f"{title[:40]}... | {url}"
            if entry not in self.history_log:
                self.history_log.insert(0, entry)
                self.history_list.insertItem(0, entry)

    def load_history_item(self, item):
        url = item.text().split("| ")[-1]
        self.tabs.currentWidget().setUrl(QUrl(url))

    def navigate_to_url(self):
        u = self.url_bar.text()
        if u == "about:home":
            self.tabs.currentWidget().setHtml(self.get_home_html())
        elif "." not in u and not u.startswith("about:"):
            # Resolve URL based on engine
            prefix = "https://www.google.com/search?q="
            if self.search_engine == "Bing": prefix = "https://www.bing.com/search?q="
            elif self.search_engine == "DuckDuckGo": prefix = "https://duckduckgo.com/?q="
            self.tabs.currentWidget().setUrl(QUrl(prefix + u))
        else:
            if not (u.startswith('http') or u.startswith('about:')): u = "https://" + u
            self.tabs.currentWidget().setUrl(QUrl(u))

    def update_ui_state(self, qurl, browser):
        current_url = qurl.toString()
        title = browser.page().title()
        
        if current_url: self.log_history(title if title else "Webpage", current_url)
        if browser != self.tabs.currentWidget(): return
        self.url_bar.setText("about:home" if current_url.startswith("data:text/html") else current_url)

    def add_new_tab(self, qurl=None, label="Start Page"):
        browser = QWebEngineView()
        browser.urlChanged.connect(lambda q, b=browser: self.update_ui_state(q, b))
        browser.titleChanged.connect(lambda t, b=browser: self.tabs.setTabText(self.tabs.indexOf(b), t[:20]))
        browser.iconChanged.connect(lambda icon, b=browser: self.tabs.setTabIcon(self.tabs.indexOf(b), icon))
        browser.page().profile().downloadRequested.connect(self.handle_download)
        
        if qurl is None or qurl.toString() == "about:home":
            browser.setHtml(self.get_home_html())
            self.url_bar.setText("about:home")
        else:
            browser.setUrl(qurl)

        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

    def handle_download(self, download):
        download.setDownloadDirectory(str(Path.home() / "Downloads"))
        download.accept()

    def close_current_tab(self, i):
        if self.tabs.count() > 1: self.tabs.removeTab(i)

def main():
    app = QApplication(sys.argv)
    window = ZenithBrowser()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
