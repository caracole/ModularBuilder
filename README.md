# ModularBuilder

**Un outil universel de build modulaire avec interface graphique**

> *« Éviter de faire tout ce que l'ordinateur peut faire »* — Pierre-Henri Giraud, 1966

## Qu'est-ce que ModularBuilder ?

ModularBuilder est un outil de développement léger qui assemble des projets web modulaires en un seul fichier HTML. Il suit le principe **expansion–compression** :

- **Expansion** (split) : un fichier HTML monolithique est décomposé en un skeleton + N modules autonomes (CSS, HTML, JS)
- **Compression** (build) : le skeleton + les modules sont réassemblés en un fichier unique déployable

L'outil fournit une **interface graphique web** qui permet de gérer tout le cycle de développement sans toucher au terminal :

- 🔨 **Build** — assembler skeleton + modules
- 🌐 **Tester** — ouvrir dans le navigateur local
- 🚀 **Publier** — déployer sur GitHub Pages en un clic
- ⚡ **Tout faire** — Build + Publier + Tester en un seul bouton
- ✏️ **Éditer** — modifier les modules directement dans l'interface
- 📦 **Gérer** — lister, filtrer, créer, supprimer des modules
- ⚙️ **Configurer** — adapter à n'importe quel projet

## Architecture

```
mon-projet/
  skeleton.html          ← structure avec marqueurs <INCLUDE:modules/xxx />
  modules/
    core-css.css         ← module CSS autonome
    nav-html.html        ← module HTML autonome
    app-js.js            ← module JS autonome
    ...
  output.html            ← fichier assemblé (résultat du build)
  modular_server.py      ← serveur local (backend)
  modular_ui.html        ← interface graphique (frontend)
```

Le format d'inclusion dans le skeleton est simple :
```html
<INCLUDE:modules/mon-module.css />
```

Chaque module porte en tête un commentaire d'identification :
```html
<!-- INCLUDE:modules/mon-module.css -->
```

## Installation

### Prérequis
- Python 3 (déjà installé sur Linux/macOS)
- Git (pour la publication GitHub)
- Un navigateur moderne

### Mise en place

```bash
# Copiez les deux fichiers dans votre dossier de projet
cp modular_server.py ~/mon-projet/
cp modular_ui.html ~/mon-projet/

# Lancez le serveur
cd ~/mon-projet
python3 modular_server.py
```

L'interface s'ouvre automatiquement dans votre navigateur à `http://127.0.0.1:7777`.

### Configuration

Au premier lancement, allez dans ⚙️ **Configuration** pour adapter les chemins à votre projet :

| Paramètre | Description | Exemple |
|---|---|---|
| Nom du projet | Nom affiché | `MediFolio` |
| Dossier de travail | Racine du projet modulaire | `~/Escritorio/MediFolio/MediFolio_modular` |
| Skeleton | Fichier skeleton | `skeleton.html` |
| Fichier output | Résultat du build | `MediFolio.html` |
| Dossier modules | Sous-dossier des modules | `modules` |
| Repo GitHub | Clone local du repo | `~/Escritorio/MediFolio_github` |
| Navigateur | Commande du navigateur | `brave-browser` |

La configuration est sauvée dans `~/.modular_builder.json` et persiste entre les sessions.

## Utilisation

### Workflow quotidien

1. **Modifiez** un module dans l'éditeur intégré
2. Cliquez **⚡ Tout faire** (Build + Publier + Tester)
3. C'est tout.

### Créer un nouveau projet from scratch

1. Créez un dossier avec un `skeleton.html` minimal
2. Ajoutez des modules dans `modules/`
3. Configurez ModularBuilder (⚙️)
4. Cliquez 🔨 Build

### Appliquer un patch (zip de modules)

Si vous recevez un zip avec des modules modifiés :
```bash
cd ~/mon-projet/modules
unzip -o ~/Descargas/patch.zip
```
Puis cliquez 🔨 Build dans l'interface.

## Cas d'usage

ModularBuilder a été créé pour le projet [MediFolio](https://caracole.github.io/MediFolio/), une application web de suivi médical longitudinal de 12.000 lignes assemblée à partir de 77 modules autonomes.

L'outil est générique et peut s'adapter à tout projet suivant l'architecture skeleton + modules.

## Origine

ModularBuilder est né de la collaboration entre **Pierre-Henri Giraud** (ingénieur informaticien, 83 ans, Castellón, Espagne) et **Claude** (Anthropic). Il incarne une philosophie de développement formulée en 1966 : automatiser tout ce qui peut l'être pour libérer l'humain.

Le développement a été réalisé en « programmation conversationnelle » — l'ingénieur conçoit, spécifie et teste ; l'IA code. Ce mode de collaboration démontre qu'un professionnel expérimenté peut produire des outils complexes grâce à l'IA générative, en conservant le contrôle total de l'architecture.

## Licence

GNU General Public License v3.0 — voir [LICENSE](LICENSE)

## Contact

- Email : MediFolio@proton.me
- MediFolio : https://caracole.github.io/MediFolio/
- DOI MediFolio : 10.5281/zenodo.19973451

---

*ModularBuilder v1.0 · Mai 2026 · Pierre-Henri Giraud × Claude (Anthropic)*
