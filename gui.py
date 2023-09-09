import eel
import threading
import time
import webbrowser
import spotify_auto_volume
import webview

from spotify_auto_volume import start_key_listener
from spotify_auth import setup_database, app

# Initialize Eel
eel.init('web')


class App:

    def __init__(self):
        # You can add any initialization code here
        setup_database()  # initializes database

    @staticmethod
    @eel.expose
    def start_flask():
        time.sleep(1)  # give a small delay for the server to start up
        webview.create_window('Spotify Authorization', 'http://127.0.0.1:8080/')


    @staticmethod
    @eel.expose
    def start(volume):
        try:
            spotify_auto_volume.adjustment_value = int(volume) if volume else 10
            print("Starting the volume controller...")

            # Start the key listener in a separate thread
            threading.Thread(target=start_key_listener, daemon=True).start()

            # Start the queue processor in a separate thread
            threading.Thread(target=spotify_auto_volume.process_volume_adjustments).start()

        except ValueError:
            eel.show_error("Error", "Please enter a valid volume adjustment value!")  # JS function placeholder

    def run(self):
        eel.start('index.html', size=(600, 400), port=8001)


if __name__ == "__main__":
    app = App()
    app.run()
