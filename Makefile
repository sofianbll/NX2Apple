SHELL := /bin/bash
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PYTHON := $(ROOT)/.venv/bin/python
MANAGER := $(ROOT)/tools/library.py
.DEFAULT_GOAL := help
export GAME FROM EXPERIMENTAL EDITION

.PHONY: help import list build all run monitor clean test
help:
	@printf '%s\n' 'make import                 Importer les fichiers terminés, sans déplacer les originaux' 'make list                   Voir les jeux et leurs identifiants' 'make build GAME=stardew      Construire seulement si nécessaire' 'make all                    Construire les jeux pris en charge et prêts' 'make run GAME=stardew        Ouvrir l’app existante ; construire seulement si absente' 'make monitor                Tableau de bord : http://127.0.0.1:8767' 'make clean GAME=stardew      Effacer uniquement les caches de ce jeu' 'make test                   Vérifier les outils locaux'
import list build all run monitor clean:
	@"$(PYTHON)" "$(MANAGER)" $@
test:
	@"$(PYTHON)" -m unittest discover -s "$(ROOT)/tools/tests" -v
	@cd "$(ROOT)/tools/build-monitor" && "$(PYTHON)" -m unittest -v test_monitor
	@if command -v node >/dev/null 2>&1; then cd "$(ROOT)/tools/build-monitor" && node --test test_components.cjs; fi
