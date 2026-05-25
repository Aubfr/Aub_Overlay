# Aub_OverlayRL

Un overlay Windows pour **Rocket League** qui affiche en temps réel ton **MMR (2v2)**, ton ratio **Wins / Losses de session**, et ta **win/loss streak**, par-dessus le jeu. L'overlay change de teinte selon ton équipe (bleue ou orange) pour rester cohérent avec le HUD du jeu.

---

## Fonctionnalités

- Affichage en haut à droite de l'écran, par-dessus Rocket League
- **MMR** récupéré depuis `tracker.gg` (segment Ranked Doubles 2v2)
- **Wins / Losses de session** comptés automatiquement à partir des variations de MMR
- **Streak de session** (🔥 Win Streak / 🧊 Loss Streak)
- **Teinte dynamique de l'overlay** selon l'équipe :
  - Bleue quand tu joues équipe Blue
  - Orange quand tu joues équipe Orange
  - Mode Auto (détection par échantillonnage de pixels) ou Manuel (via le menu de la system tray)
- **Click-through** : l'overlay ne peut pas voler le focus ni bloquer tes clics
- **Apparaît uniquement quand Rocket League est au premier plan** (alt-tab → overlay caché)
- **Blur Windows natif** derrière le panneau (effet acrylique)
- **System tray** avec icône, menu clic droit (`Team tint`, `Reset session`, `Quit`)
- **Fenêtre de statut** dans la barre des tâches Windows qui indique si RL est lancé ou non

---

## Installation (utilisateur final)

1. Télécharge `Aub_OverlayRL.exe`
2. Double-clique dessus
3. Au premier lancement, entre ton **nom d'utilisateur Epic Games** (celui qui apparaît en jeu)
4. Lance Rocket League — l'overlay apparaît automatiquement
5. Joue normalement

Pour quitter l'app : clic droit sur l'icône dans la system tray → `Quit`.

> Le username est sauvegardé dans `config.json` à côté du `.exe`. Pour le changer, supprime ce fichier et relance.

---

## Compilation depuis les sources

### Prérequis

- Python 3.10+
- Windows 10/11

### Installer les dépendances

```bash
pip install PySide6 curl_cffi psutil pywin32 pyinstaller
```

### Build

Place `Aub_OverlayRL.py` et `icone.ico` dans le même dossier, puis :

```bash
pyinstaller --onefile --noconsole --icon=icone.ico --add-data \"icone.ico;.\" --name Aub_OverlayRL Aub_OverlayRL.py
```

Ou double-clique sur `build.bat` fourni.

Le `.exe` final est dans `dist/Aub_OverlayRL.exe`.

---

## Limitations connues

- **Fonctionne en Borderless Windowed ou Windowed uniquement.** En **Fullscreen exclusif**, Windows bloque tous les overlays externes (limite système, pas du code). Passe en Borderless dans les options vidéo de Rocket League.
- La détection automatique d'équipe (bleue/orange) se base sur l'analyse de quelques pixels du HUD. Elle peut rater selon la résolution ou la caméra → dans ce cas, choisis manuellement l'équipe via la system tray (`Team tint > Blue` ou `Orange`).
- L'app dépend de l'API `tracker.gg`. Si tracker.gg est down ou bloque la requête, le MMR ne se mettra pas à jour temporairement (un cache de 30s amortit le coup).

---

## Pourquoi cette application n'est pas dangereuse

Beaucoup d'antivirus signalent les `.exe` Python compilés via PyInstaller comme « suspects », **simplement parce que PyInstaller embarque un interpréteur Python dans le binaire** — un schéma souvent vu chez les malwares. C'est un **faux positif classique**. Voici exactement ce que fait l'app et, surtout, **ce qu'elle ne fait pas** :

### Ce que fait l'app

| Action | But |
|---|---|
| Lit la liste des processus Windows | Détecter si `RocketLeague.exe` tourne (`psutil`) |
| Lit le **titre** de la fenêtre active | Savoir si Rocket League est au premier plan (`win32gui.GetForegroundWindow`) |
| Fait une requête HTTPS vers `api.tracker.gg` | Récupérer ton MMR public (site déjà accessible dans un navigateur) |
| Lit quelques pixels de l'écran (~6 points près du boost meter) | Détecter la couleur de ton équipe pour teinter l'overlay |
| Écrit deux fichiers à côté du `.exe` | `config.json` (ton pseudo Epic) + `cache.json` (cache MMR 30s) |
| Affiche une fenêtre Qt transparente | L'overlay lui-même |

### Ce que l'app **ne fait pas**

- ❌ **Aucune lecture de la mémoire de Rocket League** (pas de cheat, pas de DLL injectée, pas de hook)
- ❌ **Aucune modification du jeu** ni de ses fichiers
- ❌ **Aucune interaction réseau avec les serveurs Psyonix/Epic** (l'app ne parle qu'à `tracker.gg`)
- ❌ **Pas de keylogger, pas de capture clavier/souris**
- ❌ **Aucun envoi de données personnelles** vers un serveur tiers
- ❌ **Aucun accès aux fichiers du système** (sauf les 2 fichiers JSON dans son propre dossier)
- ❌ **Aucune persistance au démarrage** (l'app ne s'inscrit pas dans le registre ou le démarrage Windows)
- ❌ **Compatible avec les Terms of Service de Rocket League** : c'est un overlay externe purement lecture, pas un mod / cheat / trainer (même catégorie qu'OBS, Discord overlay, etc.)

### Code source ouvert

Le code source complet est dans `Aub_OverlayRL.py` (~500 lignes lisibles). Tu peux le compiler toi-même avec la commande ci-dessus → tu n'as pas à faire confiance au `.exe` que je distribue, **tu peux rebuild le tien**.

### Pour vérifier toi-même

- Inspecte le `.exe` avec [VirusTotal](https://www.virustotal.com/) (attends-toi à 0-3 faux positifs sur ~70 moteurs, c'est le bruit habituel pour un build PyInstaller)
- Surveille les connexions réseau avec **Wireshark** ou **TCPView** → tu ne verras que des requêtes HTTPS vers `api.tracker.gg`
- Surveille les accès fichiers avec **Process Monitor** → tu ne verras que `config.json` et `cache.json` dans le dossier de l'app

---

## Pourquoi la « capture de pixels » n'est pas un risque pour ta vie privée

L'overlay lit quelques pixels de l'écran pour détecter la couleur de ton équipe. Voilà précisément ce qui se passe et **pourquoi c'est totalement inoffensif** :

### Ce qui est lu

- **6 pixels** uniquement, dans une zone précise du HUD de Rocket League (bottom-right, près du boost meter)
- **Toutes les 1,5 secondes**, et **uniquement quand Rocket League est au premier plan**
- L'app récupère **les composantes R/G/B** de ces pixels, rien d'autre

### Ce qui n'est PAS fait

- ❌ **Aucune capture d'écran complète n'est jamais effectuée** (pas de `screenshot()`, pas de `BitBlt` sur la fenêtre entière)
- ❌ **Aucune image n'est sauvegardée sur le disque**
- ❌ **Aucune image n'est envoyée sur le réseau** (l'app ne parle qu'à `tracker.gg` pour récupérer du JSON)
- ❌ **Les pixels lus sont immédiatement réduits à un score \"blue hits\" / \"orange hits\"** puis jetés
- ❌ **Si tu n'es pas dans Rocket League, l'analyse de pixels est désactivée** (vérifié à chaque tick via `is_rl_focused()`)

### Le code exact qui fait ça

Tu peux le retrouver dans `Aub_OverlayRL.py`, fonction `detect_team_color()`. Il utilise l'API Windows standard `GetPixel` pour 6 coordonnées précises, compare les valeurs RGB à des seuils, et retourne uniquement la chaîne `\"blue\"`, `\"orange\"` ou `None`. Pas de buffer image, pas de stockage, pas de transmission.

### Et si tu veux désactiver complètement ça

Clic droit sur l'icône system tray → `Team tint > Off`. La fonction `detect_team_color()` ne sera plus jamais appelée. Tu peux aussi sélectionner manuellement `Blue` ou `Orange` pour figer la teinte sans aucun sampling.

---

## Données stockées localement

Deux fichiers, **uniquement à côté du `.exe`**, **jamais transmis** :

- `config.json` → `{ \"username\": \"TonPseudoEpic\" }`
- `cache.json` → `{ \"TonPseudoEpic\": { \"mmr\": 1234.5, \"timestamp\": 1234567890 } }` (cache anti-spam de l'API tracker.gg)

Pour tout effacer : supprime ces deux fichiers.

---

## Désinstallation

Supprime le dossier qui contient `Aub_OverlayRL.exe`, `config.json` et `cache.json`. C'est tout. Aucune trace ailleurs sur ton système.

---

## Crédits

- API : [tracker.gg](https://tracker.gg/)
- UI : [PySide6](https://wiki.qt.io/Qt_for_Python) (Qt)
- HTTP : [curl_cffi](https://github.com/yifeikong/curl_cffi)
- Détection process : [psutil](https://github.com/giampaolo/psutil)
- Win32 API : [pywin32](https://github.com/mhammond/pywin32)
- Build : [PyInstaller](https://pyinstaller.org/)

---

## Licence

Usage personnel. Pas de redistribution sans permission.
