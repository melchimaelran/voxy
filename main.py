"""
Voxy - Enregistreur audio avec effets de voix.
Point d'entrée principal de l'application.
"""

import sys
import os
import atexit
import shutil
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

from gui.app import VoxyApp
from config import TEMP_DIR

def cleanup_temp_dir():
    """Nettoie le répertoire temporaire à la fermeture de l'application"""
    try:
        if TEMP_DIR and os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
            print(f"🧹 Répertoire temporaire nettoyé: {TEMP_DIR}")
    except Exception as e:
        print(f"⚠️  Erreur lors du nettoyage: {e}")

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    missing_deps = []
    
    try:
        import dearpygui
    except ImportError:
        missing_deps.append("dearpygui")
    
    try:
        import sounddevice
    except ImportError:
        missing_deps.append("sounddevice")

    try:
        import soundfile
    except ImportError:
        missing_deps.append("soundfile")

    try:
        import librosa
    except ImportError:
        missing_deps.append("librosa")

    try:
        import scipy
    except ImportError:
        missing_deps.append("scipy")

    if missing_deps:
        print("❌ Dépendances manquantes:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n📦 Installez-les avec: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("🎤 Démarrage de Voxy...")
    
    # Enregistrer la fonction de nettoyage pour la fermeture
    atexit.register(cleanup_temp_dir)
    
    # Vérifications préliminaires
    if not check_dependencies():
        sys.exit(1)

    try:
        # Lancer l'application
        app = VoxyApp()
        print("✅ Interface graphique lancée")
        app.run()
        
    except KeyboardInterrupt:
        print("\n👋 Arrêt de l'application")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        sys.exit(1)
    finally:
        # Nettoyage explicite en cas d'exception
        cleanup_temp_dir()

if __name__ == "__main__":
    main()
