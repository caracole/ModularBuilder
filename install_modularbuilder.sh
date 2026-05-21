#!/bin/bash
# ╔══════════════════════════════════════════════════════════╗
# ║  ModularBuilder — Installation interactive              ║
# ║  « Éviter de faire tout ce que l'ordinateur peut faire » ║
# ╚══════════════════════════════════════════════════════════╝

clear
echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║     ModularBuilder — Installation v1.2          ║"
echo "  ║     Outil universel de build modulaire          ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""

# ── 1. Vérifications ──
echo "  1️⃣  Vérification des prérequis..."
echo ""

# Python 3
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 --version 2>&1)
    echo "  ✅ $PY_VER"
else
    echo "  ❌ Python 3 non trouvé."
    echo "     Installez-le : sudo apt install python3"
    echo ""
    read -p "  Appuyez sur Entrée pour quitter..." dummy
    exit 1
fi

# Git
if command -v git &> /dev/null; then
    GIT_VER=$(git --version 2>&1)
    echo "  ✅ $GIT_VER"
else
    echo "  ⚠️  Git non installé (optionnel, pour publier sur GitHub)"
    echo ""
    read -p "  Installer Git maintenant ? (o/n) : " INSTALL_GIT
    if [ "$INSTALL_GIT" = "o" ] || [ "$INSTALL_GIT" = "O" ]; then
        sudo apt install -y git
        echo ""
        read -p "  Votre nom complet (pour Git) : " GIT_NAME
        read -p "  Votre email (pour Git) : " GIT_EMAIL
        git config --global user.name "$GIT_NAME"
        git config --global user.email "$GIT_EMAIL"
        git config --global credential.helper store
        echo "  ✅ Git configuré"
    fi
fi

# Navigateur
BROWSER=""
for b in brave-browser google-chrome firefox chromium-browser; do
    if command -v $b &> /dev/null; then
        BROWSER=$b
        echo "  ✅ Navigateur : $b"
        break
    fi
done
if [ -z "$BROWSER" ]; then
    echo "  ⚠️  Aucun navigateur détecté automatiquement"
    BROWSER="xdg-open"
fi

echo ""
echo "  ──────────────────────────────────────────────────"
echo ""

# ── 2. Choix du dossier ──
echo "  2️⃣  Où installer ModularBuilder ?"
echo ""
DEFAULT_DIR="$HOME/Escritorio/ModularBuilder"
read -p "  Dossier [$DEFAULT_DIR] : " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_DIR}

mkdir -p "$INSTALL_DIR"
echo "  ✅ Dossier : $INSTALL_DIR"
echo ""

# ── 3. Copier les fichiers ──
echo "  3️⃣  Installation des fichiers..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$SCRIPT_DIR/modular_server.py" ]; then
    cp "$SCRIPT_DIR/modular_server.py" "$INSTALL_DIR/"
    echo "  ✅ modular_server.py"
else
    echo "  ❌ modular_server.py introuvable dans $SCRIPT_DIR"
    echo "     Placez ce script dans le même dossier que modular_server.py et modular_ui.html"
    read -p "  Appuyez sur Entrée pour quitter..." dummy
    exit 1
fi

if [ -f "$SCRIPT_DIR/modular_ui.html" ]; then
    cp "$SCRIPT_DIR/modular_ui.html" "$INSTALL_DIR/"
    echo "  ✅ modular_ui.html"
else
    echo "  ❌ modular_ui.html introuvable"
    read -p "  Appuyez sur Entrée pour quitter..." dummy
    exit 1
fi

echo ""

# ── 4. Créer un premier projet ? ──
echo "  4️⃣  Voulez-vous créer un premier projet ?"
echo ""
read -p "  Nom du projet (ou Entrée pour passer) : " PROJECT_NAME

if [ -n "$PROJECT_NAME" ]; then
    PROJECT_DIR="$INSTALL_DIR/$PROJECT_NAME"
    mkdir -p "$PROJECT_DIR/modules"

    # Créer un skeleton minimal
    cat > "$PROJECT_DIR/skeleton.html" << 'SKELEOF'
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Mon Projet</title>
</head>
<body>
<!-- Ajoutez vos INCLUDE ici -->
</body>
</html>
SKELEOF

    echo "  ✅ Projet créé : $PROJECT_DIR"
    echo "     skeleton.html + modules/"
    echo ""

    # Config
    CONFIG_FILE="$HOME/.modular_builder.json"
    cat > "$CONFIG_FILE" << CFGEOF
{
  "project_name": "$PROJECT_NAME",
  "work_dir": "$PROJECT_DIR",
  "skeleton": "skeleton.html",
  "output": "${PROJECT_NAME}.html",
  "modules_dir": "modules",
  "github_dir": "",
  "online_url": "",
  "browser": "$BROWSER",
  "include_pattern": "<INCLUDE:(.+?)\\\\s*/>"
}
CFGEOF
    echo "  ✅ Configuration sauvée : $CONFIG_FILE"

    # GitHub ?
    echo ""
    read -p "  Créer un repo GitHub pour ce projet ? (o/n) : " CREATE_GH
    if [ "$CREATE_GH" = "o" ] || [ "$CREATE_GH" = "O" ]; then
        echo ""
        echo "  📋 Instructions pour créer le repo GitHub :"
        echo ""
        echo "  1. Allez sur https://github.com/new"
        echo "  2. Nom : $PROJECT_NAME"
        echo "  3. Public, avec README"
        echo "  4. Créez le repo"
        echo ""
        read -p "  Quand c'est fait, entrez l'URL du repo (ex: https://github.com/user/repo) : " REPO_URL
        if [ -n "$REPO_URL" ]; then
            GH_DIR="$HOME/Escritorio/${PROJECT_NAME}_github"
            git clone "$REPO_URL" "$GH_DIR"
            echo "  ✅ Repo cloné : $GH_DIR"
            # Mettre à jour la config
            python3 -c "
import json
with open('$CONFIG_FILE','r') as f: c=json.load(f)
c['github_dir']='$GH_DIR'
with open('$CONFIG_FILE','w') as f: json.dump(c,f,indent=2)
"
            echo "  ✅ Config mise à jour avec le repo GitHub"
        fi
    fi
fi

echo ""
echo "  ──────────────────────────────────────────────────"
echo ""

# ── 5. Créer un raccourci bureau ──
echo "  5️⃣  Création du raccourci bureau..."
DESKTOP_FILE="$HOME/Escritorio/ModularBuilder.desktop"
cat > "$DESKTOP_FILE" << DTEOF
[Desktop Entry]
Type=Application
Name=ModularBuilder
Comment=Outil de build modulaire
Exec=bash -c 'cd "$INSTALL_DIR" && python3 modular_server.py'
Icon=utilities-terminal
Terminal=true
Categories=Development;
DTEOF
chmod +x "$DESKTOP_FILE"
echo "  ✅ Raccourci créé : ModularBuilder.desktop"

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║  ✅ Installation terminée !                     ║"
echo "  ║                                                  ║"
echo "  ║  Pour lancer ModularBuilder :                    ║"
echo "  ║  • Double-cliquez sur l'icône du bureau          ║"
echo "  ║  • Ou : cd $INSTALL_DIR && python3 modular_server.py"
echo "  ║                                                  ║"
echo "  ║  L'interface s'ouvre dans votre navigateur       ║"
echo "  ║  à http://127.0.0.1:7777                        ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""
echo "  « Éviter de faire tout ce que l'ordinateur peut faire »"
echo "  — Pierre-Henri Giraud, 1966"
echo ""

read -p "  Lancer ModularBuilder maintenant ? (o/n) : " LAUNCH
if [ "$LAUNCH" = "o" ] || [ "$LAUNCH" = "O" ]; then
    cd "$INSTALL_DIR"
    python3 modular_server.py
fi
