# UNITOOL - Documentation Utilisateur

## 1. Objectif
UNITOOL est une application desktop (Python + CustomTkinter) pour centraliser du renseignement Star Citizen :
- gestion de dossiers joueurs
- gestion des organisations
- suivi de contrats
- collecte de donnees RSI (scan)
- gestion flotte / composants / loadout
- calcul d'interception quantique

L'application stocke ses donnees localement dans une base SQLite.

---

## 2. Prerequis
- Windows 10/11
- Google Chrome installe (necessaire pour le module Intelligence)
- Connexion internet (pour les scans RSI)

---

## 3. Installation (.exe)
1. Dezipper le package UNITOOL (si archive ZIP).
2. Ouvrir le dossier de l'application.
3. Lancer `UNITOOL.exe`.

Remarque:
- selon la version distribuee, Windows peut afficher un avertissement SmartScreen.
- si besoin, cliquer `Informations complementaires` puis `Executer quand meme`.

---

## 4. Demarrage
Mode standard utilisateur:
- double-clic sur `UNITOOL.exe`

Mode developpeur (optionnel):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Au premier lancement, UNITOOL cree automatiquement:
- `unitool_data.db` (base locale SQLite)
- `unitool.log` (journal technique)

---

## 5. Vue d'ensemble de l'interface
Menu lateral principal:
- `DATABASE` (Scanner cibles, organisations et vaisseaux)
- `CONTRACTS` (Bounty board)
- `ARCHIVE` (saisie manuelle + import/export CSV)
- `INTEL` (scraping RSI)
- `INTERCEPTION` (calcul snare quantique)
- `SHIP LOADOUT` (gestion loadout, composants, configuration slots)

Panneau droit (global):
- compteur `KNOWN CONTACTS` (joueurs en base)
- compteur `KNOWN ORGANIZATIONS` (organisations en base)
- compteur `ACTIVE CONTRACTS` (affiche en rouge si > 0)
- terminal `SYSTEM LOGS` : logs de l'application en temps reel
- pied de page version : `VER ALPHA 1.0.0 - OPS STATUS: NOMINAL`

Note: l'interface bascule automatiquement en mode compact si la fenetre est plus etroite que 1200 px (panneau Intel passe en bas).

---

## 6. Guide par module

### 6.1 DATABASE (Scanner)
Permet de rechercher et modifier rapidement les donnees deja presentes dans la base.
Trois onglets : `PLAYERS`, `ORGANIZATIONS`, `SHIPS`.

#### Onglet PLAYERS
- Champ de recherche : saisir un handle ou SID (filtrage en temps reel a chaque frappe)
- Boutons :
  - `IMPORT CSV` : importe des joueurs depuis un fichier CSV
  - `EXPORT CSV` : exporte toute la base joueurs en CSV
- Resultats affiches par fiche :
  - indicateur de couleur alignement (ALLY=vert, ENEMY=rouge, NEUTRAL=blanc)
  - handle cliquable → ouvre la fenetre d'edition `EDIT IFF DATA`
  - organisation + SID cliquable → ouvre le profil RSI de l'orga
  - lien `RSI` cliquable → ouvre le profil RSI du joueur
  - vaisseau, niveau de menace, Win/Loss ratio, PVP level, activite, langue
  - jusqu'a 3 dernieres notes Intel (cliquables → gestionnaire de notes)
  - contrats actifs/clos lies a ce joueur

#### Fenetre d'edition joueur
Accessible par clic sur le handle. Champs editables :
- Organisation, SID, Rank orga, Vaisseau, Threat, Alignment, PVP Level, Activity, Language
- Handle et date de creation en lecture seule
- Section `INTEL JOURNAL` : notes existantes avec date
- Bouton `MANAGE NOTES` → gestionnaire de notes dedie
- Boutons `SAVE CHANGES` / `CANCEL`

#### Gestionnaire de notes joueur
- Zone de saisie + bouton `ADD NOTE`
- Liste des notes datees avec boutons `EDIT` / `DELETE` par note
- Confirmation avant suppression

#### Onglet ORGANIZATIONS
- Champ de recherche par nom ou SID (filtrage en temps reel)
- Boutons `IMPORT CSV` / `EXPORT CSV`
- Resultats affiches par fiche :
  - indicateur d'alignement colore
  - nom cliquable → ouvre la fenetre d'edition d'orga
  - SID cliquable → ouvre le profil RSI de l'organisation
  - type, specialisation, TAG, date de derniere mise a jour
  - roster des membres (jusqu'a 15) : Handle | Rank, puis resume Total/Visible/Redacted
  - description/Manifest (tronquee a 200 caracteres)
  - Allies / Enemies
  - jusqu'a 3 dernieres notes Intel (cliquables → gestionnaire de notes orga)

#### Gestionnaire de notes organisation
Identique au gestionnaire joueur : `ADD NOTE`, liste datee, `EDIT`, `DELETE` par note.

#### Onglet SHIPS
Embarque directement le composant catalogue vaisseaux (voir section 6.6 SHIPS pour le detail).

---

### 6.2 CONTRACTS
Tableau de pilotage des missions/contrats.

Fonctions principales:
- creation de contrat (`ACCEPT`)
- auto-completion target/client
- priorites (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- cloture d'un contrat (`CLOSE`)
- suppression d'une entree historique (`[DEL]`)
- calcul automatique du `TOTAL COLLECTED`

Gestion des types:
- bouton `EDIT TYPES`
- ajout/suppression de types de missions
- auto-remplissage de la recompense selon type

---

### 6.3 ARCHIVE
Ecran de saisie manuelle et de gestion CSV.

#### Onglet PLAYERS
Champs de saisie :
- Identite & Menace : Player Handle (Enter = charger fiche depuis DB), Threat Level (LOW/MEDIUM/HIGH/CRITICAL)
- Donnees RSI : Organization, SID, Rank
- Infos complementaires : Language, Affiliates
- Combat Stats : Wins, Losses
- Profil : Alignment (ALLY/NEUTRAL/ENEMY), PVP Level (NOOB/ROOKIE/VETERAN/ACE), Activity (PIRATE/BOUNTY HUNTER/MINER/TRADER)
- Vaisseau : Current Ship
- Notes : zone de texte libre (INTEL NOTES)

Boutons :
- `SYNCHRONIZE DATABASE` : sauvegarde avec detection de doublon et confirmation
- `CLEAR` : remet tous les champs a zero
- `IMPORT CSV` / `EXPORT CSV`

#### Onglet ORGANIZATIONS
Champs de saisie :
- Identite : SID, TAG, Organization Name
- Classification : Type (ORGANIZATION/SYNDICATE/FACTION/PMC), Alignement
- Profil : Specialization
- Diplomatie : Allies (TAGS), Enemies (TAGS)
- Notes : zone de texte `MANIFEST & INTELLIGENCE NOTES`

Boutons :
- `REGISTER ORGANIZATION` : sauvegarde avec date automatique
- `CLEAR`
- `IMPORT CSV` / `EXPORT CSV`

#### Onglet SHIPS
Formulaire complet a 27 parametres (voir section 6.6 SHIPS pour le detail complet des champs).
Boutons :
- `OCR SCREENSHOT IMPORT` : extrait automatiquement les stats depuis un screenshot du jeu
- `SYNC SHIP TO DATABASE` : sauvegarde le vaisseau
- `CLEAR`
- `IMPORT CSV` / `EXPORT CSV`

---

### 6.4 INTEL
Module de collecte automatique RSI avec Selenium.

#### TRACK PLAYER
- saisir un handle puis `SCANNER`
- l'application recupere: date d'enlistment, langue, org, SID, rang
- `SAVE CONTACT` enregistre les donnees scannees en base
- double-clic sur le nom d'orga pour basculer vers scan org

#### TRACK ORG
- saisir SID puis `EXTRACT MEMBERS`
- extraction roster visible + membres redactes
- `SAVE ORGANIZATION` stocke snapshot org en base
- `EXPORT CSV` exporte la liste roster affichee
- clic simple sur un membre: preview locale
- double-clic sur un membre: scan joueur complet

---

### 6.5 INTERCEPTION
Calcul d'une distance optimale de deploiement snare quantique.

#### Configuration d'une route
- Champ `Road name` : nom de la route d'interception
- Selecteur preset `Mantis` (actuel)
- Bouton `SAVE` : sauvegarde la route (Radius 20 000, Step 500, Max dist 250 000)
- Selecteur `START` : point de depart de la route + bouton `ADD START` pour ajouter la source
- Selecteur `DESTINATION` : filtre automatiquement les sources incompatibles a la selection
- Bouton `GENERATE` : lance le calcul d'interception quantum
- Bouton `CLEAR` : efface toutes les sources

#### Section START SOURCES
- Affiche le nombre de sources selectionnees
- Chaque source active dispose d'un bouton `REMOVE` individuel

#### Workflow standard
1. Saisir un nom de route
2. Selectionner le point de depart (`START`) et cliquer `ADD START` (repetez pour plusieurs sources)
3. Selectionner la destination (`DESTINATION`)
4. Cliquer `GENERATE`
5. Lire le resultat dans le terminal de sortie

#### Terminal de sortie
- Rapport detaille du calcul (distance optimale, parametres utilises)
- Logs de chaque action

#### Section REGISTERED ROAD PRESETS
- Liste scrollable de toutes les routes sauvegardees
- Chaque carte affiche : nom, destination, nombre de sources, Radius, Step, Max
- Boutons par route :
  - `LOAD` : charge la route dans les selecteurs
  - `EDIT` : edition inline (nom, destination, Radius/Step/Max, sources)
  - `DELETE` : suppression avec validation

#### Gestionnaire de positions
Bouton `EDIT POSITIONS` → permet d'ajouter, editer et supprimer des locations.
- Champs : nom, type, parent, coordonnees X/Y/Z
- **OCR supporté** : bouton d'import desde un screenshot Star Citizen (overlay F3 du jeu)
  - Activer l'overlay debug avec la touche `F3` dans le jeu
  - Faire un screenshot
  - UNITOOL extrait automatiquement les coordonnees X/Y/Z et le nom de la localisation

---

### 6.6 SHIPS / SHIP LOADOUT
Gestion flotte avancee accessible via `SHIP LOADOUT` dans le menu (ou depuis l'onglet SHIPS de DATABASE pour le catalogue).
Trois onglets : `SHIPS`, `LOADOUT`, `CONFIG`.

#### Onglet SHIPS — Catalogue et fiches techniques
- Champ de recherche par nom ou role (filtrage en temps reel)
- Boutons : `IMPORT CSV` / `EXPORT CSV`
- Resultats par vaisseau :
  - Nom, marque, classe de taille, role, carriere
  - Stats : Cargo (SCU), Claim time, Expedite time, Expedition Fee, crew
  - Stats de vol : SCM speed, Nav max speed, HP, Pitch/Yaw/Roll, Boosted Pitch/Yaw/Roll
  - Default Loadout par categorie avec chaque slot (equipe ou EMPTY)
  - **Double-clic** → ouvre la fenetre d'edition du vaisseau

#### Fenetre d'edition vaisseau
Trois sous-onglets :
- `GENERAL` : Manufacturer, Model Name, Size Class, Role(s), Carriere
- `FLIGHT` : SCM Speed, Boost Fwd/Bwd, Nav Speed, H2 Capacity, QT Fuel, Pitch/Yaw/Roll
- `LOGISTICS` : HP, Power, CM, Cargo, Mass, Dimensions, Expedition Fee, Claim Time, Expedite Time

#### Ajout/Edition manuelle d'un vaisseau (27 parametres)

| Section | Champs |
|---|---|
| Identite | Ship Name (Enter = charger), Manufacturer |
| Role(s) | 2 combos role, Career, Size, Crew |
| Propulsion | SCM Speed, Boost Fwd/Bwd, Nav Max Speed, H2 Capacity, QT Fuel |
| Flight Dynamics | Pitch, Yaw, Roll + Boosted Pitch/Yaw/Roll |
| Survivabilite | Total HP, Power, CM Decoy/Noise, Cargo (SCU), Mass, Dimensions |
| Economie | Expedition Fee, Claim Time, Expedite Time |

Boutons :
- `OCR SCREENSHOT IMPORT` : ouvre un selecteur d'image et extrait automatiquement tous les champs depuis un screenshot MOBIGLAS/stats du jeu
- `SYNC SHIP TO DATABASE` : sauvegarde le vaisseau
- `CLEAR` : remet tous les champs a zero

#### Onglet LOADOUT — Equipement des vaisseaux
**Panneau gauche :**
- Champ de recherche vaisseau avec autosuggestion (navigation clavier, indicateur X/total)
- Selecteur de profil de loadout (combo)
- Champ `NEW PROFILE NAME` + bouton `CREATE PROFILE`
- Terminal `CURRENT CONFIGURATION` : resume texte du loadout actuel

**Panneau droit :**
- Zone scrollable `HARDPOINT CONFIGURATION`
- Pour chaque slot defini : categorie, type, composant equipe (ou EMPTY)
- Bouton `EDIT COMPONENTS` → ouvre le gestionnaire de composants

#### Gestionnaire de composants (`EDIT COMPONENTS`)
**Ajout :**
- Slot Category (combo : SYSTEMS/WEAPON/PROPULSION/MODULE)
- Module Type (filtre par categorie)
- Model Name, Manufacturer
- Size (0-5), Grade (A/B/C/D)
- Bouton `SAVE TO DATABASE`

**Catalogue :**
- Liste scrollable par categorie : Nom, Marque, Type, Taille, Grade
- Boutons `EDIT` (edition inline avec SAVE/CANCEL/DELETE) et `DELETE` (avec confirmation)

#### Onglet CONFIG — Configuration des slots
**Panneau gauche — Categories et types :**
- Champ `NEW CATEGORY NAME` + bouton `ADD CATEGORY`
- Selecteur de categorie + champ `NEW TYPE NAME` + bouton `ADD TYPE`
- Selecteur types existants + bouton `DELETE TYPE`

**Panneau droit — Slots par vaisseau :**
- Formulaire : SHIP, CATEGORY, TYPE, MAX QTY, MAX SIZE + bouton `SAVE SLOT`
- Zone scrollable `REGISTERED SLOT SPECS` : liste groupee par vaisseau
- Chaque ligne editable inline avec boutons `EDIT` / `DELETE`

---

## 7. Import/Export CSV (resume)

### Players (Archive)
Format attendu (separateur `;`):
- `pseudo`
- `org`
- `ship`
- `threat`
- `notes`
- `alignment`

### Organizations (Archive)
Format attendu:
- `sid`
- `name`
- `tag`
- `alignment`

### Ships
Import: CSV a en-tetes correspondant aux colonnes de la table `ships`.
Export: genere automatiquement les en-tetes depuis la base.

Important:
- Utiliser des en-tetes exacts
- Eviter les cellules fusionnees/format Excel exotique
- Encodage recommande: UTF-8

---

## 8. Fichiers generes par l'application
- `unitool_data.db`: base de donnees locale
- `unitool.log`: logs techniques
- exports CSV: emplacements choisis via les boites de dialogue

---

## 9. Depannage

### L'application ne demarre pas
- verifier que vous lancez bien `UNITOOL.exe`
- essayer un lancement en tant qu'administrateur
- verifier que les fichiers de l'application sont extraits dans un dossier local (pas en lecture seule)

### Le scan INTEL ne retourne rien
- verifier connexion internet
- verifier Chrome installe et a jour
- relancer un scan (certaines pages RSI peuvent etre lentes)

### Import CSV en erreur
- verifier le separateur (souvent `;`)
- verifier les noms de colonnes
- verifier les valeurs numeriques (ex: reward, stats)

### Base corrompue ou tests a blanc
- fermer l'application
- sauvegarder puis supprimer `unitool_data.db`
- relancer l'application pour regen la base

### Mode developpeur uniquement
Si vous utilisez la version source Python (pas le .exe):
- verifier l'environnement virtuel actif
- verifier `pip install -r requirements.txt`
- lancer depuis le dossier racine du projet

---

## 10. Bonnes pratiques utilisateur
- Toujours valider les scans avec un controle visuel avant sauvegarde
- Utiliser les notes pour tracer les decisions intel
- Exporter regulierement les donnees critiques (players/orgs/ships)
- Eviter les doubles saisies: rechercher avant de creer

---

## 11. Raccourci de lancement (optionnel)
Pour la version .exe, vous pouvez:
- creer un raccourci Windows vers `UNITOOL.exe`
- le placer sur le Bureau ou dans la barre des taches