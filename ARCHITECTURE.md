"""ARCHITECTURE – Séparation des Contrôleurs et des Vues"""

## 📊 Structure MVC Refactorisée

```
├── main.py                    # Point d'entrée (App window)
│
├── controllers/
│   ├── __init__.py
│   ├── app_controller.py      # Main AppController (orchestre tout)
│   ├── scanner_controller.py  # Logique de recherche/édition cibles
│   ├── logger_controller.py   # Logique d'archivage/import/export
│   ├── contract_controller.py # Logique des contrats/bounty
│   └── intelligence_controller.py # Logique scraping/renseignements
│
├── views/
│   ├── main_view.py           # Vue principale (orchestre les frames)
│   ├── scanner_frame.py       # UI recherche cibles
│   ├── logger_frame.py        # UI archivage dossiers
│   ├── contract_frame.py      # UI bounty board
│   └── intelligence_frame.py  # UI scraping/intelligence
│
├── database.py                # Couche données (SQLite)
└── drake_ui/                  # Composants UI réutilisables
```

## 🎮 Architecture en Couches

```
┌─ APP LAYER ──────────────────────────────────────────┐
│ App (main.py)                                         │
│  └─ MainView (container de frames)                   │
│     ├─ ScannerFrame     ──┐                          │
│     ├─ LoggerFrame      ──┼─ Reçoivent AppController│
│     ├─ ContractFrame    ──┤                          │
│     └─ IntelligenceFrame ─┘                          │
│                                                       │
├─ CONTROLLER LAYER ───────────────────────────────────┤
│ AppController                                         │
│  ├─ scanner: ScannerController      (search_targets) │
│  ├─ logger: LoggerController        (save_target)    │
│  ├─ contract: ContractController    (add_contract)   │
│  └─ intelligence: IntelligenceController (...)       │
│                                                       │
├─ DATA LAYER ──────────────────────────────────────────┤
│ Database: SQLite (query, commit, upsert_target...)    │
│                                                       │
└───────────────────────────────────────────────────────┘
```

## 📝 Exemple d'Utilisation

### Avant (direct à DB) :
```python
# Dans ScannerFrame
rows = self.controller.db.query(
    "SELECT * FROM targets WHERE pseudo LIKE ?",
    (f"%{q}%",)
)
```

### Après (via sub-controller) :
```python
# Dans ScannerFrame
rows = self.controller.scanner.search_targets(q)
```

## 🚀 Avantages

1. **Séparation des responsabilités clairement définie**
   - Chaque controller gère la logique d'une vue
   - Les vues reste lean et focalisées sur l'UI

2. **Réutilisabilité**
   - Les controllers peuvent être utilisés indépendamment
   - Facilite les tests unitaires

3. **Maintenabilité**
   - Logique métier centralisée par domaine
   - Mise à jour facilitée des requêtes SQL

4. **Extensibilité**
   - Ajouter un nouveau controller = ajouter une nouvelle feature
   - Pas besoin de toucher aux vues existantes

## 📌 Endpoints Disponibles

### ScannerController
- `search_targets(query:str)` → list
- `get_target_full(pseudo:str)` → list
- `update_target(pseudo, **fields)` → None
- `export_targets_csv()` → list

### LoggerController  
- `save_target(pseudo, org, sid, ...)` → None
- `load_target(pseudo)` → list
- `import_targets_csv(rows)` → None
- `export_targets_csv()` → list

### ContractController
- `add_contract(target, client, reward, ...)` → None
- `get_active_contracts()` → list
- `get_closed_contracts()` → list
- `complete_contract(contract_id, target)` → None
- `delete_contract(contract_id)` → None
- `get_contract_types()` → list
- `add_contract_type(name, reward)` → None

### IntelligenceController
- `save_player_intel(data:dict)` → None
- `get_player_intel(handle:str)` → dict
- `update_player_intel(pseudo, **fields)` → None
- `save_organization_roster(org_sid, members)` → None

## 🔄 Accès Direct à la DB (Compatibilité)

Les views peuvent toujours accéder directement à la DB si nécessaire :

```python
# Accès brut encore disponible
self.controller.db.cursor
self.controller.db.conn
self.controller.query(sql, params)
self.controller.commit(sql, params)
```

Mais c'est recommandé d'utiliser les sub-controllers pour la maintenabilité.
