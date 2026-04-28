# UNITOOL — Star Citizen Tactical Assistant

> Utilitaire desktop tout-en-un pour joueurs Star Citizen.  
> Renseignement, contrats, flotte, interception quantique — tout en local, sans API officielle.

---

## Téléchargement

> **Les utilisateurs n'ont pas besoin de Python.**  
> Téléchargez simplement la dernière version dans la section [Releases](../../releases) et lancez `UNITOOL.exe`.

⚠️ Windows peut afficher un avertissement SmartScreen au premier lancement.  
Cliquez sur **Informations complémentaires** puis **Exécuter quand même**.

---

## Fonctionnalités

| Module | Description |
|---|---|
| **DATABASE** | Recherche et édition des dossiers joueurs et organisations |
| **CONTRACTS** | Suivi des contrats PvP et missions avec calcul des gains |
| **ARCHIVE** | Saisie manuelle, import et export CSV |
| **INTEL** | Collecte automatique de données RSI via Selenium |
| **INTERCEPTION** | Calcul de distance snare pour l'interception quantique |
| **SHIP LOADOUT** | Catalogue de vaisseaux, gestion des composants et loadouts |

---

## Prérequis (version EXE)

- Windows 10 ou 11
- Google Chrome installé *(requis uniquement pour le module INTEL)*
- Connexion internet *(requis uniquement pour le module INTEL)*

Toutes les données sont stockées **localement** dans une base SQLite générée automatiquement au premier lancement.

---

## Installation

1. Téléchargez le fichier `.zip` depuis les [Releases](../../releases)
2. Dézippez dans le dossier de votre choix
3. Lancez `UNITOOL.exe`

Au premier démarrage, l'application crée automatiquement :
- `unitool_data.db` — base de données locale
- `unitool.log` — journal technique

---

## Démarrage rapide

### MODULE DATABASE
Recherchez un joueur ou une organisation déjà enregistrée. Cliquez sur un pseudo pour ouvrir son dossier complet et le modifier.

### MODULE INTEL
Saisissez un handle de joueur ou un SID d'organisation puis cliquez **SCANNER**. Les données RSI sont récupérées automatiquement et peuvent être sauvegardées en base en un clic.

### MODULE INTERCEPTION
1. Sélectionnez votre point de départ et cliquez **ADD START**
2. Sélectionnez la destination
3. Cliquez **GENERATE** pour obtenir les coordonnées de snare optimales

### MODULE SHIP LOADOUT
Sélectionnez un vaisseau, choisissez un profil de loadout, équipez les slots par catégorie. Créez autant de profils que nécessaire (COMBAT, CARGO, EXPLORATION…).

---

## Données et confidentialité

Unitool ne collecte et n'envoie aucune donnée. Tout est stocké localement sur votre machine dans le fichier `unitool_data.db`. Ce fichier peut être sauvegardé, déplacé ou supprimé à tout moment.

---

## Dépannage

**L'application ne démarre pas**
- Vérifiez que les fichiers sont extraits dans un dossier local (pas dans un zip, pas sur un réseau)
- Essayez un lancement en tant qu'administrateur

**Le module INTEL ne retourne rien**
- Vérifiez votre connexion internet
- Vérifiez que Google Chrome est installé et à jour
- Relancez le scan (les pages RSI peuvent être lentes)

**Réinitialiser la base de données**
- Fermez l'application
- Sauvegardez puis supprimez `unitool_data.db`
- Relancez — la base est recréée automatiquement

---

## Pour les développeurs

<details>
<summary>Lancer depuis les sources</summary>

**Prérequis**
- Python 3.11+
- Tesseract OCR installé et dans le PATH *(requis pour l'OCR)*

**Installation**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

**Tests**
```powershell
pytest tests/
```

**Structure du projet**
```
controllers/     Logique métier par domaine
views/           Interface utilisateur (CustomTkinter)
models/          Modèles de données
repositories/    Accès base de données par domaine
services/        Services techniques (OCR, helpers)
db_migrations.py Système de migrations versionnées
database.py      Point d'entrée base de données
main.py          Point d'entrée application
```
</details>

---

## Alpha — Avertissement

Unitool est en version **alpha**. Certaines fonctionnalités peuvent être incomplètes ou instables. Vos retours sont les bienvenus — ouvrez une [Issue](../../issues) pour signaler un bug ou suggérer une amélioration.

---

*Unitool est un projet communautaire indépendant, non affilié à Cloud Imperium Games.*
