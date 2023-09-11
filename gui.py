import sys
import threading

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from spotify_auto_volume import start_key_listener, process_volume_adjustments
from spotify_auto_volume import scheduler as volume_scheduler

HEROKU_SERVER_URL = "https://spotifyautovolume-efd5d02c1318.herokuapp.com/"

class SpotifyAutoVolumeApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Title
        self.title_label = QLabel('Spotify Auto Volume Controller', self)
        layout.addWidget(self.title_label)

        # Volume Adjustment Input
        self.volume_adjustment = QLineEdit(self)
        self.volume_adjustment.setPlaceholderText('Volume Adjustment')
        layout.addWidget(self.volume_adjustment)

        # Start Button
        self.start_btn = QPushButton('Start', self)
        self.start_btn.clicked.connect(self.start_volume_controller)
        layout.addWidget(self.start_btn)

        # Authorize with Spotify Button
        self.auth_btn = QPushButton('Authorize with Spotify', self)
        self.auth_btn.clicked.connect(self.authorize_spotify)
        layout.addWidget(self.auth_btn)

        # Status Message
        self.status_message = QLabel('', self)
        layout.addWidget(self.status_message)

        self.setLayout(layout)
        self.setWindowTitle('Spotify Auto Volume Controller')
        self.show()
 

    def start_volume_controller(self):

        # Start the key listener and volume adjustments
        key_listener_thread = threading.Thread(target=start_key_listener, daemon=True)
        key_listener_thread.start()
        volume_thread = threading.Thread(target=process_volume_adjustments)
        volume_thread.start()
        self.status_message.setText('Volume controller started.')

    def authorize_spotify(self):
        # Open the Heroku server's authorization URL in the user's default browser
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(f"{HEROKU_SERVER_URL}/authorize"))
        self.browser.show()


if __name__ == '__main__':
   
    app = QApplication(sys.argv)
    window = SpotifyAutoVolumeApp()
    sys.exit(app.exec_())
