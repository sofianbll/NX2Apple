SHELL := /bin/bash
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PYTHON := $(ROOT)/.venv/bin/python
MANAGER := $(ROOT)/tools/library.py
APP_PACKAGE := $(ROOT)/tools/desktop-app
APP_BUNDLE := $(ROOT)/dist/NXNative Dashboard.app
APP_DMG := $(ROOT)/dist/NXNative Dashboard.dmg
.DEFAULT_GOAL := help
export GAME FROM EXPERIMENTAL EDITION

.PHONY: help import list build all run monitor clean test rzr-probe app dmg app-test
help:
	@printf '%s\n' 'make import                 Importer les fichiers terminés, sans déplacer les originaux' 'make list                   Voir les jeux et leurs identifiants' 'make build GAME=stardew      Construire seulement si nécessaire' 'make all                    Construire les jeux pris en charge et prêts' 'make run GAME=stardew        Ouvrir l’app existante ; construire seulement si absente' 'make monitor                Tableau de bord : http://127.0.0.1:8767' 'make clean GAME=stardew      Effacer uniquement les caches de ce jeu' 'make test                   Vérifier les outils locaux' 'make rzr-probe              Sonde manette R/ZR en lecture seule' 'make app                    Construire et signer NXNative Dashboard.app' 'make dmg                    Construire et vérifier le DMG installable' 'make app-test               Tester le cycle de vie de l’app construite'
import list build all run monitor clean:
	@"$(PYTHON)" "$(MANAGER)" $@
test:
	@"$(PYTHON)" -m unittest discover -s "$(ROOT)/tools/tests" -v
	@cd "$(ROOT)/tools/build-monitor" && "$(PYTHON)" -m unittest -v test_monitor
	@cd "$(ROOT)/tools/build-monitor" && node --test test_components.cjs
rzr-probe:
	@mkdir -p "$(ROOT)/.build"
	@swiftc "$(ROOT)/tools/rzr-probe/rzr-probe.swift" -o "$(ROOT)/.build/rzr-probe"
	@"$(ROOT)/.build/rzr-probe"
app:
	@swift build --package-path "$(APP_PACKAGE)" --configuration release --arch arm64
	@build_dir="$$(swift build --package-path "$(APP_PACKAGE)" --configuration release --arch arm64 --show-bin-path)"; \
	bundle="$(APP_BUNDLE)"; \
	binary="$$bundle/Contents/MacOS/NXNativeDashboard"; \
	rm -rf "$$bundle"; \
	mkdir -p "$$bundle/Contents/MacOS"; \
	cp "$$build_dir/NXNativeDashboard" "$$binary"; \
	cp "$(APP_PACKAGE)/Info.plist" "$$bundle/Contents/Info.plist"; \
	mkdir -p "$$bundle/Contents/Resources"; \
	cp "$(APP_PACKAGE)/AppIcon.icns" "$$bundle/Contents/Resources/AppIcon.icns"; \
	plutil -lint "$$bundle/Contents/Info.plist"; \
	test "$$(lipo -archs "$$binary")" = "arm64"; \
	codesign --sign - --force "$$bundle"; \
	codesign --verify --strict "$$bundle"
	@test "$$(plutil -extract NSAppTransportSecurity json -o - "$(APP_BUNDLE)/Contents/Info.plist")" = '{"NSAllowsLocalNetworking":true}'
	@printf '%s\n' 'App construite : $(APP_BUNDLE)'
dmg: app
	@bash "$(APP_PACKAGE)/package_dmg.sh" "$(APP_BUNDLE)" "$(APP_DMG)"
app-test: app
	@"$(PYTHON)" "$(APP_PACKAGE)/app_test.py" "$(APP_BUNDLE)"
