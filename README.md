# Aubverlay

> **Overlay stats Rocket League** — MMR en temps réel, suivi W/L de session, streak et lueur dynamique.

<img width="1609" height="1082" alt="image" src="https://github.com/user-attachments/assets/404afc2d-977c-433d-84b9-e6850327d45b" />

<img width="766" height="97" alt="image" src="https://github.com/user-attachments/assets/9cb1c1c8-bcbe-443c-b4b6-2245425631e8" />

---

## ✨ Fonctionnalités

- 🎯 **MMR en direct** via l'API tracker.gg (pseudo Epic Games)
- 📊 **Suivi de session** — Wins, Losses, Streak, Delta MMR
- 🌟 **Lueur dynamique** — orange si streak positif, bleu si négatif, neutre sinon
- 🎨 **6 styles d'overlay** — Blade, Bar, Tiles, Compact, Pill, Hexagon
- 📐 **Positionnement libre** — sliders X/Y ou glisser-déposer en mode édition
- 🔁 **Détection automatique** — l'overlay apparaît uniquement quand Rocket League est au premier plan
- 🕹️ **Actions manuelles** — ajouter/supprimer des wins/losses, reset de session
- 🌍 **Bilingue** — Français / English
- 🗂️ **Dossier de données configurable** — AppData par défaut ou chemin personnalisé
- 🖥️ **Dashboard complet** avec animation de démarrage et halos animés

---

## 🚀 Installation

### Méthode recommandée — `.exe` standalone

1. Télécharge le dernier `Aubverlay.exe` dans les [Releases](../../releases)
2. Double-clique → l'assistant de premier lancement s'ouvre
3. Entre ton pseudo Epic Games exactement tel qu'en jeu
4. Lance Rocket League — l'overlay apparaît automatiquement

> ⚠️ **Aucune installation requise.** Un seul fichier `.exe`, pas de dépendances.
> ⚠️ **Il faut quitter l'application en cliquant sur quitter et pas sur la fenêtre sinon l'appplication tournera en fond !**

---


## ⚙️ Configuration

Les fichiers de configuration sont stockés dans `%LOCALAPPDATA%\Aubverlay\` par défaut.

| Fichier | Contenu |
|---------|---------|
| `config.json` | Préférences utilisateur (pseudo, style, position, langue…) |
| `cache.json` | Cache MMR tracker.gg (TTL : 30 secondes) |
| `bootstrap.json` | Pointeur vers le dossier de données si personnalisé |

Tu peux changer l'emplacement depuis **Réglages → Dossier de données**.

---

## 🎮 Utilisation

### Premier lancement
L'assistant te guide en 4 étapes :
1. Présentation de l'app
2. Choix du dossier de données
3. Saisie du pseudo Epic Games *(obligatoire)*
4. Conseils d'utilisation

### Dashboard
- **Bannière** — état de Rocket League, connexion tracker.gg et mode de lueur
- **Stats** — Wins / Losses / Streak / MMR / Rang en temps réel
- **Actions manuelles** — corriger le compteur si une partie n'est pas détectée

### Overlay
- S'affiche automatiquement quand Rocket League est au premier plan
- **Mode Borderless Windowed** recommandé dans RL
- Positionnement via les sliders ou en cliquant **"Déplacer l'overlay à la souris"**

### Playlists supportées
| Ranked | Casual | Extra modes |
|--------|--------|-------------|
| 1v1, 2v2, 3v3 | 1v1, 2v2, 3v3 | Hoops, Rumble, Dropshot, Snow Day |

> Les playlists **Casual** n'ont pas de suivi W/L automatique (pas de rang compétitif).

---

## 🌟 Styles d'overlay

| Style | Description |
|-------|-------------|
| **Default** | Parallélogramme incliné — style esport signature |
| **Bar** | Barre horizontale arrondie |
| **Tiles** | Tuiles séparées par stat |
| **Compact** | Version minimale, petite taille |
| **Pill** | Colonnes verticales empilées |
| **Hexagon** | Forme hexagonale angulaire |

---

## 🔧 Détails techniques

- **API** : tracker.gg (`/api/v2/rocket-league/standard/profile/epic/{username}`)
- **Détection RL** : scan des processus via `psutil` toutes les 3 secondes
- **Détection focus** : `win32gui.GetForegroundWindow()` toutes les 500 ms (nécessite `pywin32`)
- **Cache MMR** : TTL de 30 secondes, stocké en JSON local
- **Rendu overlay** : 100% Qt (`QPainter`, `WA_TranslucentBackground`), pas de BlurBehind Windows
- **Données** : aucune persistance de session (reset au lancement de RL)

---

## ❓ FAQ

**L'overlay ne s'affiche pas**
→ Vérifie que Rocket League est en **Borderless Windowed** et au premier plan. Si `pywin32` n'est pas installé, l'overlay est toujours visible (Status → pywin32 : non installé).

**Le MMR n'est pas récupéré**
→ Le pseudo Epic Games doit être **exactement** celui affiché sur tracker.gg. Vérifie dans Réglages.

**Les W/L ne sont pas comptés**
→ La détection est basée sur les changements de MMR. En **Casual**, le suivi automatique est désactivé.

**L'overlay apparaît derrière le jeu**
→ Passe Rocket League en **Borderless Windowed** (pas Fullscreen exclusif).

---

## 🤝 Support & Communauté

Rejoins le Discord pour du support, des annonces et retours :

[![Discord](https://img.shields.io/badge/Discord-Rejoindre-5865F2?logo=discord&logoColor=white)](https://discord.gg/uMQBhs3UqH)

---


*Fait avec par **Aub** — non affilié à Psyonix / Epic Games / tracker.gg*
