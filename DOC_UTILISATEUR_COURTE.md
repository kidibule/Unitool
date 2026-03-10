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
- DATABASE: rechercher, lire et modifier les dossiers deja en base
- CONTRACTS: creer/suivre/cloturer les missions
- ARCHIVE: saisie manuelle + import/export CSV
- INTEL: scanner RSI (joueurs et organisations)
- INTERCEPTION: calcul de distance snare
- SHIPS: flotte, composants, loadouts et configuration des slots

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
- Saisir au moins 2 caracteres pour rechercher
- Cliquer un pseudo/nom pour ouvrir la fiche editable
- Bouton EXPORT DB pour extraire un CSV des targets

### CONTRACTS
- Renseigner TARGET, CLIENT, REWARD, PRIORITE
- ACCEPT pour creer
- CLOSE pour cloturer
- EDIT TYPES pour gerer les modeles de mission

### ARCHIVE
- PLAYERS, ORGANIZATIONS, SHIPS
- Permet la saisie manuelle propre
- Import/Export CSV dans chaque onglet

### INTEL
- TRACK PLAYER: scan profil RSI puis SAVE CONTACT
- TRACK ORG: scan roster puis SAVE ORGANIZATION
- Double-clic membre: lance un scan joueur

### INTERCEPTION
- Ajouter une ou plusieurs sources
- Choisir destination
- GENERATE SNARE COORDINATES
- Lire la distance optimale en KM dans le terminal

### SHIPS
- SHIPS: recherche + import/export flotte
- LOADOUT: equipement des composants par slot
- CONFIG: creation categories/types + limites de slots

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
- Import CSV en erreur: verifier en-tetes et separateur
- Base a reinitialiser: fermer app, sauvegarder puis supprimer unitool_data.db, relancer

---

## 7. Bonnes pratiques
- Rechercher avant de creer une fiche
- Ajouter des notes courtes et datees
- Exporter regulierement les donnees critiques
- Verifier les scans avant sauvegarde