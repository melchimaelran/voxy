# Interface d'enregistrement audio
import dearpygui.dearpygui as dpg
from core.recorder import AudioRecorder
from config import THEME_TEXT_COLOR, THEME_PRIMARY, SPECTRAL_WIDTH
from gui.player_ui import AudioPlayer
import threading
import time


class RecorderUI:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.current_audio_file = None

        self.spectral_data = []  # Placeholder for spectral data

        self.audio_player = None
        self.recording_start_time = None
        self.timer_thread = None
        self.is_recording = False

    def start_recording_callback(self):
        """Callback pour démarrer l'enregistrement"""
        if self.recorder.start_recording():
            self.is_recording = True
            self.recording_start_time = time.time()

            # remove player_ui
            self.spectral_data = []
            dpg.delete_item("player_ui", children_only=True)
            dpg.set_item_label("record_button", "Arrêter")  # Caractère carré
            dpg.set_value("status_text", "Enregistrement en cours...")  # Point rouge
            dpg.configure_item("record_button", callback=self.stop_recording_callback)

            # Afficher le timer et démarrer le thread de mise à jour
            dpg.show_item("timer_text")
            self.start_timer()

    def stop_recording_callback(self):
        """Callback pour arrêter l'enregistrement"""
        self.is_recording = False
        audio_file = self.recorder.stop_recording()

        if audio_file:
            self.current_audio_file = audio_file
            self.audio_player = AudioPlayer(audio_file)

            # Mettre à jour l'interface
            self.audio_player.create_ui()

            print(self.current_audio_file)
            dpg.set_item_label("record_button", "Enregistrer")  # Point pour micro
            dpg.set_value("status_text", "Enregistrement terminé")  # Checkmark
            dpg.configure_item("record_button", callback=self.start_recording_callback)

            # Cacher le timer
            # dpg.hide_item("timer_text")

    def update_spectral_visualization(self):
        """Met à jour la visualisation spectrale"""
        if self.spectral_data and len(self.spectral_data) > 0:
            dpg.delete_item("spectral_container", children_only=True)
            dpg.set_item_height("spectral_container", 45)
            # last 46 elements in self.spectral_data
            last_46_data = (
                self.spectral_data[-46:]
                if len(self.spectral_data) > 46
                else self.spectral_data
            )
            for i in range(len(last_46_data)):
                spectral_position = i * SPECTRAL_WIDTH
                max_spectral_value = max(last_46_data) if last_46_data else 1

                spectralLength = (
                    (40 * (last_46_data[i])) / max_spectral_value
                    if last_46_data[i]
                    else 0
                )

                dpg.draw_rectangle(
                    (spectral_position, 100),
                    (SPECTRAL_WIDTH + spectral_position, 40 - spectralLength),
                    color=(0, 255, 0, 255),
                    fill=(100, 255, 100, 200),
                    parent="spectral_container",
                )

    def start_timer(self):
        """Démarre le thread du minuteur"""

        def update_timer():
            while self.is_recording:
                if self.recording_start_time:
                    elapsed = time.time() - self.recording_start_time
                    minutes = int(elapsed // 60)
                    seconds = int(elapsed % 60)
                    self.spectral_data.append(self.recorder.get_recording_level())

                    self.update_spectral_visualization()
                    timer_text = f"Temps: {minutes:02d}:{seconds:02d}"  # Texte simple

                    # Mettre à jour l'affichage du timer
                    if dpg.does_item_exist("timer_text"):
                        dpg.set_value("timer_text", timer_text)

                time.sleep(0.1)  # Mise à jour toutes les 100ms

        self.timer_thread = threading.Thread(target=update_timer, daemon=True)
        self.timer_thread.start()

    def create_ui(self):
        """Crée l'interface d'enregistrement"""
        # Status text
        dpg.add_text("Prêt à enregistrer", tag="status_text", color=THEME_TEXT_COLOR)
        dpg.add_spacer(height=5)

        # If spectral_data is not empty, display the spectral data
        with dpg.drawlist(tag="spectral_container", width=350, height=0):
            []

        # Timer text (caché par défaut)
        dpg.add_text("Temps: 00:00", tag="timer_text", color=THEME_PRIMARY, show=False)
        dpg.add_spacer(height=5)

        with dpg.group(tag="player_ui"):
            []

        with dpg.theme() as rouge_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(
                    dpg.mvThemeCol_Button, (117, 38, 38), category=dpg.mvThemeCat_Core
                )

        # Bouton d'enregistrement principal
        dpg.add_button(
            label="Enregistrer",
            tag="record_button",
            callback=self.start_recording_callback,
            width=108,
            height=50,
        )
        dpg.bind_item_theme("record_button", rouge_theme)

        dpg.add_spacer(height=10)
