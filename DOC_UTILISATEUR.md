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
- `DATABASE` (Scanner cibles + organisations)
- `CONTRACTS` (Bounty board)
- `ARCHIVE` (saisie manuelle + import/export CSV)
- `INTEL` (scraping RSI)
- `INTERCEPTION` (snare distance)
- `SHIPS` (catalogue flotte, composants, loadout)

Panneau droit (global):
- compteurs (contacts, organisations, contrats actifs)
- logs systeme en temps reel

---

## 6. Guide par module

### 6.1 DATABASE (Scanner)
Permet de rechercher et modifier rapidement les donnees deja presentes dans la base.

#### Onglet TARGETS
- Champ de recherche: saisir au moins 2 caracteres
- Resultats affiches: pseudo, org/sid, stats combat, notes intel, historique contrats
- Actions:
  - clic sur pseudo: edition complete du dossier
  - clic sur `[RSI]`: ouverture page citoyen RSI
  - clic sur org/sid: ouverture page org RSI
  - `EXPORT DB`: export CSV simplifie des targets

#### Onglet ORGANIZATIONS
- Recherche par nom ou SID
- Affichage detaille: type, specialisation, roster visible, diplomatie, notes
- Clic sur nom: edition de la fiche organisation
- Clic sur SID: ouverture RSI org

#### Edition des fiches
Dans les fenetres d'edition target/org:
- modification des champs metier
- gestion des notes (ajout, edition, suppression)
- bouton de synchronisation pour enregistrer en base

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
- creation/mise a jour dossier joueur
- chargement d'un dossier via `TARGET HANDLE` + Enter
- import/export CSV
- nettoyage formulaire (`CLEAR`)

#### Onglet ORGANIZATIONS
- creation/mise a jour fiche org
- import/export CSV
- nettoyage formulaire

#### Onglet SHIPS
- creation/mise a jour fiche vaisseau
- import/export CSV
- chargement par nom (Enter)

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
Calcul d'une distance optimale de deploiement snare.

Workflow:
1. Selectionner un point de depart
2. Ajouter des sources (`ADD`) (option: inclure les lunes si source = planete)
3. Selectionner une destination
4. Activer/desactiver les sources voulues
5. Cliquer `GENERATE SNARE COORDINATES`

Resultat:
- distance optimale en KM
- instructions de deploiement affichees dans le terminal

Gestion des positions:
- bouton `EDIT POSITIONS`
- ajout d'une position (nom, type, parent, X/Y/Z)
- suppression d'une position (si non liee comme parent)

---

### 6.6 SHIPS
Gestion flotte avancée en 3 onglets.

#### SHIPS
- recherche par nom/role
- affichage fiche technique
- import/export CSV flotte
- affichage du loadout par defaut (slots vides inclus)

#### LOADOUT
- selection vaisseau
- profils de loadout (creation, chargement)
- equipement des slots par categorie/sous-type
- purge complete des slots (`CLEAR ALL SLOTS`)
- acces au manager composants (`EDIT COMPONENTS`)

#### CONFIG
- creation categories et types de composants
- configuration des slots par vaisseau:
  - categorie
  - type
  - quantite max
  - taille max
- sauvegarde/suppression des specifications

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