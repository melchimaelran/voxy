# Makefile pour Voxy - enregistreur audio + effets de voix

.PHONY: help run install setup venv clean dev test lint format deps-check deps-install check

# Variables
PYTHON := python3
VENV_DIR := .venv
VENV_ACTIVATE := $(VENV_DIR)/bin/activate
REQUIREMENTS := requirements.txt
MAIN_SCRIPT := main.py

# Couleurs pour l'affichage
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RED := \033[31m
RESET := \033[0m

# Commande par défaut
help: ## 📖 Affiche l'aide
	@echo "$(BLUE)🎤 Voxy - Makefile Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Commandes principales:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# === COMMANDES PRINCIPALES ===

run: ## 🚀 Lance l'application Voxy (avec activation du venv)
	@echo "$(GREEN)🎤 Lancement de Voxy...$(RESET)"
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		echo "$(BLUE)📦 Activation de l'environnement virtuel...$(RESET)"; \
		. $(VENV_ACTIVATE) && $(PYTHON) $(MAIN_SCRIPT); \
	else \
		echo "$(YELLOW)⚠️  Pas d'environnement virtuel trouvé, utilisation du Python système...$(RESET)"; \
		$(PYTHON) $(MAIN_SCRIPT); \
	fi

dev: ## 🔧 Lance en mode développement (avec vérifications)
	@echo "$(GREEN)🔧 Mode développement...$(RESET)"
	@$(MAKE) deps-check
	@$(MAKE) run

# === INSTALLATION ET CONFIGURATION ===

setup: ## 🛠️ Installation complète (venv + dépendances)
	@echo "$(GREEN)🛠️ Configuration complète de Voxy...$(RESET)"
	@$(MAKE) venv
	@$(MAKE) deps-install
	@echo "$(GREEN)✅ Installation terminée! Utilisez 'make run' pour lancer l'application$(RESET)"

venv: ## 🐍 Crée l'environnement virtuel Python
	@echo "$(GREEN)🐍 Création de l'environnement virtuel...$(RESET)"
	@$(PYTHON) -m venv $(VENV_DIR)
	@echo "$(GREEN)✅ Environnement virtuel créé dans $(VENV_DIR)$(RESET)"

deps-install: ## 📦 Installe les dépendances Python
	@echo "$(GREEN)📦 Installation des dépendances...$(RESET)"
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && pip install --upgrade pip && pip install -r $(REQUIREMENTS); \
	else \
		$(PYTHON) -m pip install --upgrade pip && $(PYTHON) -m pip install -r $(REQUIREMENTS); \
	fi
	@echo "$(GREEN)✅ Dépendances installées$(RESET)"

install: deps-install ## 📦 Alias pour deps-install

# === VÉRIFICATIONS ===

check: ## 🔍 Vérifie l'installation et les dépendances
	@echo "$(GREEN)🔍 Vérification du système...$(RESET)"
	@$(MAKE) deps-check

deps-check: ## 🔍 Vérifie que les dépendances sont installées
	@echo "$(GREEN)🔍 Vérification des dépendances...$(RESET)"
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && $(PYTHON) -c "$(CHECK_DEPS_SCRIPT)"; \
	else \
		$(PYTHON) -c "$(CHECK_DEPS_SCRIPT)"; \
	fi

# === DÉVELOPPEMENT ===

test: ## 🧪 Lance les tests (si présents)
	@echo "$(GREEN)🧪 Lancement des tests...$(RESET)"
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && $(PYTHON) -m pytest tests/ -v 2>/dev/null || echo "$(YELLOW)⚠️  Pas de tests trouvés$(RESET)"; \
	else \
		$(PYTHON) -m pytest tests/ -v 2>/dev/null || echo "$(YELLOW)⚠️  Pas de tests trouvés$(RESET)"; \
	fi

lint: ## 🔍 Analyse du code (flake8, pylint si disponibles)
	@echo "$(GREEN)🔍 Analyse du code...$(RESET)"
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && \
		($(PYTHON) -m flake8 . --exclude=$(VENV_DIR) 2>/dev/null || echo "$(YELLOW)⚠️  flake8 non installé$(RESET)") && \
		($(PYTHON) -m pylint *.py 2>/dev/null || echo "$(YELLOW)⚠️  pylint non installé$(RESET)"); \
	else \
		($(PYTHON) -m flake8 . --exclude=$(VENV_DIR) 2>/dev/null || echo "$(YELLOW)⚠️  flake8 non installé$(RESET)") && \
		($(PYTHON) -m pylint *.py 2>/dev/null || echo "$(YELLOW)⚠️  pylint non installé$(RESET)"); \
	fi

format: ## 🎨 Formate le code (black, autopep8 si disponibles)
	@echo "$(GREEN)🎨 Formatage du code...$(RESET)"
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && \
		($(PYTHON) -m black . --exclude=$(VENV_DIR) 2>/dev/null || echo "$(YELLOW)⚠️  black non installé$(RESET)") && \
		($(PYTHON) -m autopep8 --in-place --recursive . --exclude=$(VENV_DIR) 2>/dev/null || echo "$(YELLOW)⚠️  autopep8 non installé$(RESET)"); \
	else \
		($(PYTHON) -m black . --exclude=$(VENV_DIR) 2>/dev/null || echo "$(YELLOW)⚠️  black non installé$(RESET)") && \
		($(PYTHON) -m autopep8 --in-place --recursive . --exclude=$(VENV_DIR) 2>/dev/null || echo "$(YELLOW)⚠️  autopep8 non installé$(RESET)"); \
	fi

# === MAINTENANCE ===

clean: ## 🧹 Nettoie les fichiers temporaires
	@echo "$(GREEN)🧹 Nettoyage...$(RESET)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@rm -rf *.egg-info/ 2>/dev/null || true
	@echo "$(GREEN)✅ Nettoyage terminé$(RESET)"

clean-all: clean ## 🧹 Nettoie tout (inclut l'environnement virtuel)
	@echo "$(GREEN)🧹 Nettoyage complet...$(RESET)"
	@rm -rf $(VENV_DIR)
	@echo "$(GREEN)✅ Nettoyage complet terminé$(RESET)"

# === INFORMATIONS ===

info: ## 📊 Affiche les informations du projet
	@echo "$(BLUE)📊 Informations du projet Voxy$(RESET)"
	@echo "$(YELLOW)Répertoire:$(RESET) $(shell pwd)"
	@echo "$(YELLOW)Python:$(RESET) $(shell $(PYTHON) --version)"
	@echo "$(YELLOW)Environnement virtuel:$(RESET) $(if $(wildcard $(VENV_ACTIVATE)),✅ Présent,❌ Absent)"
	@echo "$(YELLOW)Fichier principal:$(RESET) $(MAIN_SCRIPT)"
	@echo "$(YELLOW)Dépendances:$(RESET) $(REQUIREMENTS)"
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		echo "$(YELLOW)Packages installés:$(RESET)"; \
		. $(VENV_ACTIVATE) && pip list --format=columns | head -10; \
	fi

# Script Python pour vérifier les dépendances
define CHECK_DEPS_SCRIPT
import sys
missing = []
try:
    import dearpygui
    print("✅ dearpygui")
except ImportError:
    missing.append("dearpygui")
    print("❌ dearpygui")

try:
    import sounddevice
    print("✅ sounddevice")
except ImportError:
    missing.append("sounddevice")
    print("❌ sounddevice")

try:
    import librosa
    print("✅ librosa")
except ImportError:
    missing.append("librosa")
    print("❌ librosa")

try:
    import scipy
    print("✅ scipy")
except ImportError:
    missing.append("scipy")
    print("❌ scipy")

try:
    import numpy
    print("✅ numpy")
except ImportError:
    missing.append("numpy")
    print("❌ numpy")

if missing:
    print(f"\n❌ Dépendances manquantes: {', '.join(missing)}")
    print("💡 Lancez: make deps-install")
    sys.exit(1)
else:
    print("\n✅ Toutes les dépendances sont installées")
endef
export CHECK_DEPS_SCRIPT

# === RACCOURCIS ===

r: run ## 🚀 Raccourci pour 'run'

s: setup ## 🛠️ Raccourci pour 'setup'

c: check ## 🔍 Raccourci pour 'check'

i: info ## 📊 Raccourci pour 'info'
