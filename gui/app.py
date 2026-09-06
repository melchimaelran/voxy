# Composants de l'interface utilisateur
import dearpygui.dearpygui as dpg
from gui.recorder_ui import RecorderUI
from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    THEME_BUTTON_COLOR,
    THEME_APP_BG,
    THEME_BUTTON_HOVERED,
)
from pathlib import Path


class VoxyApp:
    def __init__(self):
        self.recorder_ui = RecorderUI()

    def setup_theme(self):
        """Configure le thème de l'application"""
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, THEME_APP_BG)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, THEME_BUTTON_HOVERED)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, THEME_BUTTON_HOVERED)
                dpg.add_theme_color(dpg.mvThemeCol_Button, THEME_BUTTON_COLOR)

        dpg.bind_theme(global_theme)

    def load_logo(self):
        """Charge le logo Voxy"""
        logo_path = Path(__file__).parent.parent / "assets" / "icons" / "voxy_logo.png"

        if logo_path.exists():
            # Charger l'image comme texture
            width, height, channels, data = dpg.load_image(str(logo_path))

            # Créer la texture
            with dpg.texture_registry():
                dpg.add_static_texture(
                    width=width,
                    height=height,
                    default_value=data,
                    tag="voxy_logo_texture",
                )
            return True
        else:
            print(f"Logo non trouvé: {logo_path}")
            return False

    def create_main_window(self):
        """Crée la fenêtre principale"""
        with dpg.window(
            label="Voxy",
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            tag="main_window",
        ):
            # Header avec logo
            with dpg.group(horizontal=True):
                # Charger et afficher le logo si disponible
                if self.load_logo():
                    # center the logo
                    dpg.add_image("voxy_logo_texture", width=200, height=87)
                else:
                    # Fallback avec texte si pas de logo
                    dpg.add_text("🎤 VOXY", color=[100, 149, 237])

                dpg.add_spacer(width=20)

            # spacer
            dpg.add_spacer(height=5)
            # Section d'enregistrement
            with dpg.tab_bar():
                with dpg.tab(label="Enregistrement"):
                    self.recorder_ui.create_ui()

    def run(self):
        """Lance l'application"""
        dpg.create_context()

        # Configuration
        self.setup_theme()
        self.create_main_window()

        # Configuration de la fenêtre principale
        dpg.create_viewport(title="Voxy", width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)

        # Boucle principale
        dpg.start_dearpygui()
        dpg.destroy_context()


if __name__ == "__main__":
    app = VoxyApp()
    app.run()
