# Configuration globale
from pathlib import Path

# Configuration audio
SAMPLE_RATE = 16000  # Taux d'échantillonnage recommandé
AUDIO_FORMAT = "float32"
CHANNELS = 1  # Mono

# Chunk size explication detaillée :
# - C'est la taille des données audio traitées à chaque itération.
# - Permet de gérer les flux audio en temps réel.
# - Plus petit = plus de réactivité, mais plus de charge CPU.
# - Plus grand = moins de réactivité, mais plus efficace pour le traitement.
# - 1024 est un bon compromis pour la plupart des applications.
CHUNK_SIZE = 1024
TEMP_DIR = Path.home() / "Documents" / "Voxy" / "temp"
EXPORTS_DIR = Path.home() / "Documents" / "Voxy"

# Configuration interface
WINDOW_WIDTH = 350
WINDOW_HEIGHT = 425
THEME_APP_BG = [34, 34, 34]  # Gris foncé
THEME_BUTTON_HOVERED = [82, 80, 80]
THEME_BUTTON_COLOR = [84, 84, 84]
THEME_PRIMARY = [61, 219, 225]  # Cyan
THEME_TEXT_COLOR = [255, 255, 255]  # Blanc
THEME_SECONDARY = [255, 255, 255]  # Blanc

SPECTRAL_WIDTH = 7

# Créer les dossiers nécessaires
TEMP_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
