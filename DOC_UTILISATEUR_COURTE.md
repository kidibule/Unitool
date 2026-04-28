# UNITOOL - Guide Utilisateur Court

## 1. Demarrage rapide
Prerequis:
- Windows
- Chrome installe

Installation:
- dezipper le package
- ouvrir le dossier UNITOOL

Lancement:
- double-clic sur `UNITOOL.exe`

Option developpeur (version source Python):
- python -m venv .venv
- .\.venv\Scripts\Activate.ps1
- pip install -r requirements.txt
- .\.venv\Scripts\python.exe main.py

UNITOOL cree automatiquement:
- unitool_data.db (base locale)
- unitool.log (journal technique)

---

## 2. A quoi sert chaque menu
- DATABASE: rechercher, lire et modifier les dossiers deja en base (joueurs, orgs, vaisseaux)
- CONTRACTS: creer/suivre/cloturer les missions
- ARCHIVE: saisie manuelle + import/export CSV
- INTEL: scanner RSI (joueurs et organisations)
- INTERCEPTION: calcul de distance snare quantique + gestion de routes
- SHIP LOADOUT: loadout, composants et configuration des slots

---

## 3. Workflow conseille (simple)
1. Scanner dans INTEL un joueur ou une org
2. Sauvegarder avec SAVE CONTACT ou SAVE ORGANIZATION
3. Verifier/ajuster dans DATABASE
4. Creer un contrat dans CONTRACTS si necessaire
5. Exporter periodiquement via ARCHIVE

---

## 4. Utilisation express par module

### DATABASE
- Onglets : PLAYERS, ORGANIZATIONS, SHIPS
- Saisir un handle ou SID pour rechercher (filtrage en temps reel)
- Cliquer un pseudo/nom pour ouvrir la fiche editable
- Boutons IMPORT CSV / EXPORT CSV dans chaque onglet

### CONTRACTS
- Renseigner TARGET, CLIENT, REWARD, PRIORITE
- ACCEPT pour creer (le TYPE pre-remplit automatiquement la REWARD)
- CLOSE pour cloturer
- EDIT TYPES pour gerer les modeles de mission

### ARCHIVE
- Onglets PLAYERS, ORGANIZATIONS, SHIPS (27 champs + OCR)
- Saisie manuelle ou chargement depuis DB (Enter dans le champ nom)
- Import/Export CSV dans chaque onglet
- Bouton OCR SCREENSHOT IMPORT (onglet SHIPS) : extrait les stats depuis un screenshot du jeu

### INTEL
- TRACK PLAYER: scan profil RSI puis SAVE CONTACT
- TRACK ORG: scan roster puis SAVE ORGANIZATION
- Double-clic membre: lance un scan joueur

### INTERCEPTION
- Saisir un nom de route, selectionner les sources (START + ADD START)
- Choisir destination
- GENERATE pour calculer la distance snare
- SAVE pour enregistrer la route comme preset reutilisable
- EDIT POSITIONS: ajouter des locations (OCR depuis screenshot F3 du jeu supporte)

### SHIP LOADOUT
- SHIPS: catalogue + fiche technique + import/export + OCR Screenshot Import
- LOADOUT: selection vaisseau + profil de loadout + equipement des slots + EDIT COMPONENTS
- CONFIG: gestion categories/types + configuration des slots par vaisseau

---

## 5. Formats CSV minimaux
Players:
- pseudo, org, ship, threat, notes, alignment

Organizations:
- sid, name, tag, alignment

Ships:
- utiliser un CSV avec en-tetes de colonnes de la table ships

---

## 6. Depannage ultra-court
- Lancement KO: verifier que `UNITOOL.exe` est bien lance depuis un dossier local
- Scan INTEL vide: verifier internet et Chrome
- Import CSV en erreur: verifier en-tetes et separateur (`;`)
- OCR Screenshot vide: verifier que Tesseract est installe (inclus dans le package .exe)
- OCR Positions: activer l'overlay debug avec `F3` dans le jeu avant de faire le screenshot
- Base a reinitialiser: fermer app, sauvegarder puis supprimer unitool_data.db, relancer

---

## 7. Bonnes pratiques
- Rechercher avant de creer une fiche
- Ajouter des notes courtes et datees
- Exporter regulierement les donnees critiques
- Verifier les scans avant sauvegarde