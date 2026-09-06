# Enregistrement audio (PyAudio)
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
import time
from scipy import signal
from scipy.ndimage import uniform_filter1d
from config import SAMPLE_RATE, CHANNELS, TEMP_DIR

class AudioRecorder:
    def __init__(self):
        self.is_recording = False
        self.audio_data = None
        self.current_file = None
        
    def _remove_noise(self, audio_array):
        """Supprime le bruit de l'enregistrement audio"""
        try:
            # 1. Normalisation
            audio_normalized = audio_array / np.max(np.abs(audio_array))
            
            # 2. Filtre passe-haut pour supprimer les basses fréquences (bruit de fond)
            # Fréquence de coupure à 80 Hz
            nyquist = SAMPLE_RATE * 0.5
            high_freq = 80 / nyquist
            b, a = signal.butter(4, high_freq, btype='high')
            audio_filtered = signal.filtfilt(b, a, audio_normalized.flatten())
            
            # 3. Filtre passe-bas pour supprimer les hautes fréquences (sifflement)
            # Fréquence de coupure à 8000 Hz
            low_freq = 8000 / nyquist
            b, a = signal.butter(4, low_freq, btype='low')
            audio_filtered = signal.filtfilt(b, a, audio_filtered)
            
            # 4. Suppression du bruit par seuillage adaptatif
            # Calculer le niveau de bruit de base (premier 0.5 seconde)
            noise_sample_size = int(0.5 * SAMPLE_RATE)
            if len(audio_filtered) > noise_sample_size:
                noise_level = np.std(audio_filtered[:noise_sample_size])
                
                # Appliquer un gate de bruit (réduire les signaux faibles)
                threshold = noise_level * 2.5
                audio_gated = np.where(np.abs(audio_filtered) > threshold, 
                                     audio_filtered, 
                                     audio_filtered * 0.1)
            else:
                audio_gated = audio_filtered
            
            # 5. Lissage léger pour réduire les artefacts
            if len(audio_gated) > 10:
                window_size = min(5, len(audio_gated) // 100)
                audio_smoothed = uniform_filter1d(audio_gated, size=window_size)
            else:
                audio_smoothed = audio_gated
            
            # 6. Normalisation finale
            if np.max(np.abs(audio_smoothed)) > 0:
                audio_final = audio_smoothed / np.max(np.abs(audio_smoothed)) * 0.8
            else:
                audio_final = audio_smoothed
            
            # Remettre en forme pour la sauvegarde
            if CHANNELS == 1:
                return audio_final.reshape(-1, 1)
            else:
                return audio_final.reshape(-1, CHANNELS)
                
        except Exception as e:
            print(f"⚠️  Erreur lors de la suppression du bruit: {e}")
            return audio_array  # Retourner l'audio original en cas d'erreur
    
    def start_recording(self):
        """Démarre l'enregistrement audio"""
        if self.is_recording:
            return False
            
        self.is_recording = True
        self.audio_data = []
        
        def callback(indata, frames, time, status):
            if status:
                print(f"Erreur d'enregistrement: {status}")
            if self.is_recording:
                self.audio_data.append(indata.copy())
        
        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                callback=callback,
                dtype='float32'
            )
            self.stream.start()
            return True
        except Exception as e:
            print(f"Erreur lors du démarrage: {e}")
            self.is_recording = False
            return False
    
    def stop_recording(self):
        """Arrête l'enregistrement et sauvegarde le fichier avec suppression du bruit"""
        if not self.is_recording:
            return None
            
        self.is_recording = False
        
        try:
            self.stream.stop()
            self.stream.close()
            
            if self.audio_data:
                # Concaténer toutes les données audio
                audio_array = np.concatenate(self.audio_data, axis=0)
                
                # Suppression du bruit
                print("🔧 Suppression du bruit en cours...")
                audio_cleaned = self._remove_noise(audio_array)
                
                # Créer un nom de fichier unique
                timestamp = int(time.time())
                filename = f"recording_{timestamp}.wav"
                self.current_file = TEMP_DIR / filename
                
                # Sauvegarder en WAV avec audio nettoyé
                wav.write(str(self.current_file), SAMPLE_RATE, audio_cleaned)
                print("✅ Audio nettoyé et sauvegardé")
                
                return str(self.current_file)
        except Exception as e:
            print(f"Erreur lors de l'arrêt: {e}")
            
        return None
    
    def get_current_file(self):
        """Retourne le chemin du fichier actuel"""
        return str(self.current_file) if self.current_file else None
    
    def get_recording_level(self):
        """Retourne le niveau sonore actuel pour la visualisation"""
        if self.audio_data and len(self.audio_data) > 0:
            recent_data = self.audio_data[-1] if self.audio_data else np.array([0])
            return float(np.max(np.abs(recent_data)))
        return 0.0
