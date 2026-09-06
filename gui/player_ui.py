# Lecteur audio simple avec path en paramètre
import dearpygui.dearpygui as dpg
import sounddevice as sd
import soundfile as sf
import threading
import time
import numpy as np
from pathlib import Path
import shutil
from config import EXPORTS_DIR
import subprocess
import platform
import os
import librosa
from config import TEMP_DIR


class AudioPlayer:
    def __init__(self, audio_file_path):
        self.audio_file_path = audio_file_path
        self.audio_data = None
        self.sample_rate = None
        self.duration = 0

        # État du lecteur
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        self.volume = 0.7

        # Thread et timing
        self.start_time = None
        self.pause_position = 0

        # Variables pour les effets
        self.selected_effect = "Aucun"

        # Charger le fichier
        self.load_audio_file()

    def load_audio_file(self):
        """Charge le fichier audio depuis le path"""
        try:
            print(f"Chargement du fichier audio: {self.audio_file_path}")
            if not Path(self.audio_file_path).exists():
                raise FileNotFoundError(f"Fichier non trouvé: {self.audio_file_path}")

            self.audio_data, self.sample_rate = sf.read(self.audio_file_path)

            # Convertir en mono si stéréo
            if len(self.audio_data.shape) > 1:
                self.audio_data = np.mean(self.audio_data, axis=1)

            self.duration = len(self.audio_data) / self.sample_rate

            # Mettre à jour le temps total
            self._update_total_time()

        except Exception as e:
            print(f"Erreur chargement audio: {e}")
            self.audio_data = None

    def _update_total_time(self):
        """Met à jour l'affichage du temps total"""
        if dpg.does_item_exist("total_time_player"):
            minutes = int(self.duration // 60)
            seconds = int(self.duration % 60)
            dpg.set_value("total_time_player", f"{minutes:02d}:{seconds:02d}")

    def _update_current_time(self, current_seconds):
        """Met à jour l'affichage du temps actuel"""
        if dpg.does_item_exist("current_time_player"):
            minutes = int(current_seconds // 60)
            seconds = int(current_seconds % 60)
            dpg.set_value("current_time_player", f"{minutes:02d}:{seconds:02d}")

    def play(self):
        """Démarre ou reprend la lecture"""
        if self.audio_data is None:
            return

        if self.is_paused:
            # Reprendre depuis la pause
            self.is_paused = False
            self.is_playing = True
            self._start_playback_from_position(self.pause_position)
        else:
            # Nouveau démarrage
            self.is_playing = True
            self.pause_position = 0
            self._start_playback_from_position(0)

        # Mettre à jour l'interface
        if dpg.does_item_exist("play_button"):
            dpg.set_item_label("play_button", "Pause")

    def pause(self):
        """Met en pause la lecture"""
        if self.is_playing:
            self.is_paused = True
            self.is_playing = False

            # Calculer la position de pause
            if self.start_time:
                elapsed = time.time() - self.start_time
                self.pause_position = min(self.pause_position + elapsed, self.duration)

            sd.stop()

            if dpg.does_item_exist("play_button"):
                dpg.set_item_label("play_button", "Play")

    def stop(self):
        """Arrête complètement la lecture"""
        self.is_playing = False
        self.is_paused = False
        self.pause_position = 0

        sd.stop()

        # Mettre à jour l'interface
        if dpg.does_item_exist("play_button"):
            dpg.set_item_label("play_button", "Play")
        if dpg.does_item_exist("progress_bar"):
            dpg.set_value("progress_bar", 0.0)

        # Remettre le temps actuel à 00:00
        self._update_current_time(0)

    def _start_playback_from_position(self, start_seconds):
        """Démarre la lecture depuis une position"""
        try:
            # Calculer l'index de départ
            start_index = int(start_seconds * self.sample_rate)
            audio_slice = self.audio_data[start_index:]

            if len(audio_slice) == 0:
                self.stop()
                return

            # Appliquer le volume
            audio_slice = audio_slice * self.volume

            self.start_time = time.time()
            self.expected_end_time = time.time() + (len(audio_slice) / self.sample_rate)

            # Lancer la lecture
            sd.play(audio_slice, self.sample_rate)

            # Thread amélioré pour surveiller la fin avec vérifications multiples
            def monitor_playback():
                expected_duration = len(audio_slice) / self.sample_rate
                check_interval = 0.1  # Vérifier toutes les 100ms
                checks_since_start = 0
                max_checks = (
                    int(expected_duration / check_interval) + 10
                )  # Marge de sécurité

                while self.is_playing and checks_since_start < max_checks:
                    time.sleep(check_interval)
                    checks_since_start += 1

                    # Vérifier si sounddevice a fini de jouer
                    if (
                        not sd.get_stream().active
                        if hasattr(sd.get_stream(), "active")
                        else False
                    ):
                        break

                    # Vérifier le temps écoulé
                    elapsed = time.time() - self.start_time
                    if elapsed >= expected_duration + 0.2:  # Marge de 200ms
                        break

                    # Vérifier la position calculée
                    current_pos = self.pause_position + elapsed
                    if current_pos >= self.duration:
                        break

                # Arrêter seulement si on joue encore
                if self.is_playing and not self.is_paused:
                    self.stop()

            threading.Thread(target=monitor_playback, daemon=True).start()

            # Thread pour mettre à jour la progression ET les temps
            def update_progress():
                while self.is_playing:
                    if self.start_time:
                        elapsed = time.time() - self.start_time
                        current_pos = self.pause_position + elapsed

                        # Vérifier si on a atteint la fin
                        if current_pos >= self.duration:
                            if self.is_playing:  # Double vérification
                                self.stop()
                            break

                        # Mettre à jour la barre de progression
                        if dpg.does_item_exist("progress_bar") and self.duration > 0:
                            progress = min(current_pos / self.duration, 1.0)
                            dpg.set_value("progress_bar", progress)

                        # Mettre à jour le temps actuel
                        self._update_current_time(current_pos)

                    time.sleep(0.1)

            threading.Thread(target=update_progress, daemon=True).start()

        except Exception as e:
            print(f"Erreur lecture: {e}")
            self.stop()

    # Callbacks pour l'interface
    def play_callback(self):
        """Callback du bouton play/pause"""
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def stop_callback(self):
        """Callback du bouton stop"""
        self.stop()

    def volume_callback(self, sender, value):
        """Callback du slider de volume"""
        self.set_volume(value)

    def copy_callback(self):
        """Copie le fichier audio dans le presse-papiers système"""
        try:
            if not self.audio_file_path or not Path(self.audio_file_path).exists():
                print("Aucun fichier audio à copier")
                return

            # Déterminer la commande selon l'OS
            system = platform.system()

            if system == "Linux":
                if not os.path.exists(self.audio_file_path):
                    raise FileNotFoundError(f"{self.audio_file_path} not found")

                # Format required by Nautilus and Discord for clipboard file copy
                clipboard_content = f"copy\nfile://{self.audio_file_path}"

                # Use xclip to set clipboard with special MIME type
                subprocess.run(
                    [
                        "xclip",
                        "-selection",
                        "clipboard",
                        "-t",
                        "text/uri-list",
                        # "-i",
                    ],
                    input=clipboard_content.encode(),
                    check=True,
                )

                if dpg.does_item_exist("status_text"):
                    dpg.set_value(
                        "status_text", "Fichier copié - vous pouvez le coller"
                    )

            elif system == "Windows":
                # Utiliser PowerShell pour Windows
                cmd = [
                    "powershell",
                    "-command",
                    f"Set-Clipboard -Path '{self.audio_file_path}'",
                ]

                process = subprocess.run(cmd, capture_output=True)

                if process.returncode == 0:
                    print(
                        f"Fichier copié dans le presse-papiers: {self.audio_file_path}"
                    )
                    if dpg.does_item_exist("status_text"):
                        dpg.set_value(
                            "status_text", "Fichier copié - vous pouvez le coller"
                        )
                else:
                    raise Exception(f"Erreur PowerShell: {process.stderr.decode()}")

            elif system == "Darwin":  # macOS
                # Utiliser pbcopy pour macOS
                cmd = ["pbcopy"]
                file_uri = f"file://{Path(self.audio_file_path).absolute()}"

                process = subprocess.run(
                    cmd, input=file_uri.encode("utf-8"), capture_output=True
                )

                if process.returncode == 0:
                    print(
                        f"Fichier copié dans le presse-papiers: {self.audio_file_path}"
                    )
                    if dpg.does_item_exist("status_text"):
                        dpg.set_value(
                            "status_text", "Fichier copié - vous pouvez le coller"
                        )
                else:
                    raise Exception(f"Erreur pbcopy: {process.stderr.decode()}")
            else:
                raise Exception(f"OS non supporté: {system}")

        except Exception as e:
            print(f"Erreur lors de la copie: {e}")
            if dpg.does_item_exist("status_text"):
                dpg.set_value("status_text", f"Erreur copie: {e}")

    def save_callback(self):
        """Sauvegarde le fichier audio dans le dossier de téléchargements"""
        try:
            if not self.audio_file_path or not Path(self.audio_file_path).exists():
                print("Aucun fichier audio à sauvegarder")
                return

            # Générer un nom de fichier unique
            timestamp = int(time.time())
            original_name = Path(self.audio_file_path).stem
            extension = Path(self.audio_file_path).suffix
            new_filename = f"voxy_{original_name}_{timestamp}{extension}"

            # Chemin de destination
            destination = EXPORTS_DIR / new_filename

            # Créer le dossier si nécessaire
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Copier le fichier
            shutil.copy2(self.audio_file_path, destination)

            print(f"Fichier sauvegardé dans : {destination}")

            # Optionnel: Afficher un message de confirmation
            if dpg.does_item_exist("status_text"):
                dpg.set_value("status_text", f"Fichier sauvegardé dans : {destination}")

            return str(destination)

        except Exception as e:
            print(f"Erreur sauvegarde: {e}")
            if dpg.does_item_exist("status_text"):
                dpg.set_value("status_text", f"Erreur sauvegarde: {e}")
            return None

    def apply_effect_callback(self, sender, app_data):
        """Applique un effet à l'audio et génère un nouveau fichier"""
        if not self.audio_file_path or not Path(self.audio_file_path).exists():
            print("Aucun fichier audio original")
            return

        effect = dpg.get_value("effect_combo")
        filename_by_path = Path(self.audio_file_path).stem

        if effect == "Aucun":
            self.selected_effect = effect
            input_file = TEMP_DIR / f"{filename_by_path.split('___')[0]}.wav"
            self.reset(input_file)
            if dpg.does_item_exist("status_text"):
                dpg.set_value("status_text", "Effet supprimé")
            return
        print(effect)

        try:
            if dpg.does_item_exist("status_text"):
                dpg.set_value("status_text", f"Application de l'effet {effect}...")

            effect_filename = f"{filename_by_path.split('___')[0]}___{effect.lower().replace(' ', '_')}.wav"
            effect_file_path = TEMP_DIR / effect_filename

            # Appliquer l'effet selon le type
            input_file = TEMP_DIR / f"{filename_by_path.split('___')[0]}.wav"
            print(f"Input file: {input_file}")

            if effect == "Pitch Aigu":
                self._apply_pitch_effect(input_file, effect_file_path, 4)
            elif effect == "Pitch Grave":
                self._apply_pitch_effect(input_file, effect_file_path, -4)
            elif effect == "Robot":
                self._apply_robot_effect(input_file, effect_file_path)
            elif effect == "Echo":
                self._apply_echo_effect(input_file, effect_file_path)
            elif effect == "Rapide":
                self._apply_speed_effect(input_file, effect_file_path, 1.5)
            elif effect == "Lent":
                self._apply_speed_effect(input_file, effect_file_path, 0.7)
            elif effect == "Chipmunk":
                self._apply_pitch_effect(input_file, effect_file_path, 8)
            elif effect == "Demon":
                self._apply_pitch_effect(input_file, effect_file_path, -8)

            self.selected_effect = effect

            if dpg.does_item_exist("status_text"):
                dpg.set_value(
                    "status_text",
                    f"Effet {effect} appliqué - Cliquez sur play pour un aperçu",
                )
            self.stop()

        except Exception as e:
            print(f"Erreur application effet: {e}")
            if dpg.does_item_exist("status_text"):
                dpg.set_value("status_text", f"Erreur effet: {e}")

    def reset(self, new_value):
        self.__init__(new_value)

    def _apply_pitch_effect(self, input_file, output_file, semitones):
        """Applique un effet de pitch"""
        y, sr = librosa.load(input_file, sr=None)
        y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones)
        sf.write(output_file, y_shifted, sr)
        # reset the audio file path in the __init__ to play
        self.reset(output_file)

    def _apply_robot_effect(self, input_file, output_file):
        """Applique un effet robot avec distorsion"""
        y, sr = librosa.load(input_file, sr=None)

        # Effet robot: distorsion + pitch léger
        y_robot = librosa.effects.pitch_shift(y, sr=sr, n_steps=2)

        # Ajouter de la distorsion
        y_robot = np.tanh(y_robot * 3) * 0.7

        sf.write(output_file, y_robot, sr)
        # reset the audio file path in the __init__ to play
        self.reset(output_file)

    def _apply_echo_effect(self, input_file, output_file):
        """Applique un effet d'écho"""
        y, sr = librosa.load(input_file, sr=None)

        # Créer l'écho
        delay_samples = int(0.3 * sr)  # 300ms de délai
        echo = np.zeros_like(y)

        if len(y) > delay_samples:
            echo[delay_samples:] = y[:-delay_samples] * 0.6

        # Mélanger original + écho
        y_echo = y + echo

        # Normaliser pour éviter la saturation
        y_echo = y_echo / np.max(np.abs(y_echo)) * 0.8

        sf.write(output_file, y_echo, sr)
        # reset the audio file path in the __init__ to play
        self.reset(output_file)

    def _apply_speed_effect(self, input_file, output_file, speed_factor):
        """Applique un changement de vitesse"""
        y, sr = librosa.load(input_file, sr=None)

        # Changer la vitesse
        y_speed = librosa.effects.time_stretch(y, rate=speed_factor)

        sf.write(output_file, y_speed, sr)
        # reset the audio file path in the __init__ to play
        self.reset(output_file)

    def create_ui(self, parent="player_ui"):
        """Crée l'interface du lecteur audio"""
        with dpg.group(parent=parent, horizontal=True):
            # Minutes and seconds playing
            dpg.add_text("00:00", tag="current_time_player", color=(0, 255, 0, 255))
            dpg.add_text("/", color=(0, 255, 0, 255))

            # Calculer et afficher le temps total
            if self.duration > 0:
                minutes = int(self.duration // 60)
                seconds = int(self.duration % 60)
                total_time_text = f"{minutes:02d}:{seconds:02d}"
            else:
                total_time_text = "00:00"

            dpg.add_text(
                total_time_text, tag="total_time_player", color=(0, 255, 0, 255)
            )

        # === SECTION EFFETS FUNNY ===
        dpg.add_text("Effets : ", color=[255, 200, 100], parent=parent)

        with dpg.group(parent=parent, horizontal=True):
            # Combo box pour sélectionner l'effet
            dpg.add_combo(
                items=[
                    "Aucun",
                    "Pitch Aigu",
                    "Pitch Grave",
                    "Robot",
                    "Echo",
                    "Rapide",
                    "Lent",
                    "Chipmunk",
                    "Demon",
                ],
                tag="effect_combo",
                default_value="Aucun",
                width=100,
                callback=self.apply_effect_callback,
            )

        with dpg.group(parent=parent, horizontal=True):
            dpg.add_button(
                label="Play",
                tag="play_button",
                callback=self.play_callback,
                width=60,
                height=30,
                enabled=self.audio_data is not None,
            )

            dpg.add_button(
                label="Stop",
                tag="stop_button",
                callback=self.stop_callback,
                width=60,
                height=30,
                enabled=self.audio_data is not None,
            )

            dpg.add_button(
                label="Copy",
                tag="copy_button",
                callback=self.copy_callback,
                width=60,
                height=30,
                enabled=self.audio_data is not None,
            )

            dpg.add_button(
                label="Save",
                tag="save_button",
                callback=self.save_callback,
                width=60,
                height=30,
                enabled=self.audio_data is not None,
            )
