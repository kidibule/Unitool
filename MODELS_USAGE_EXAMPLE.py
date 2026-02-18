"""Exemples d'utilisation des modèles UNITOOL.

Les modèles encapsulent la logique métier des entités et offrent
des méthodes utiles pour manipuler les données.
"""

# ===== TARGET MODEL =====
from models import Target

# Créer une cible
target = Target(
    pseudo="JohnDoe",
    org="TEORG",
    ship="F7C-M",
    alignment="AMI",
    pvp_lvl="VETERAN",
    activity="TRADER",
    threat="LOW",
)

# Utiliser les propriétés
print(target.pseudo)  # "JOHNDOE"
print(target.is_friendly())  # True
print(target.is_threat())  # False
print(target.pvp_ratio())  # 0 (wins / losses)

# Incrémenter les victoires
target.add_win()
target.add_win()
print(target.wins)  # 2
print(target.pvp_ratio())  # inf (2 / 0)

# Convertir en dict
target_dict = target.to_dict()

# Convertir en tuple (pour DB)
target_tuple = target.to_db_tuple()

# Créer depuis une row DB
db_row = ("JOHNDOE", "TEORG", "F7C-M", "LOW", "Notes...", "18/02/2026", 2, 0, "AMI", "VETERAN", "TRADER", "TE", "MEMBER", "18/02/2026", "FR", "NONE")
target2 = Target.from_db_row(db_row)


# ===== CONTRACT MODEL =====
from models import Contract

# Créer un contrat
contract = Contract(
    target="JOHNDOE",
    client="ELITE",
    reward="5000",
    priority="HIGH",
    contract_type="VHRT",
)

# Utiliser les propriétés
print(contract.is_open())  # True
print(contract.priority_numeric())  # 2 (HIGH = 2)
print(contract.get_reward_int())  # 5000

# Fermer le contrat
contract.close()
print(contract.is_closed())  # True


# ===== CONTRACT TYPE MODEL =====
from models import ContractType

# Créer un type de contrat
contract_type = ContractType("VHRT", "50000")

# Utiliser les propriétés
print(contract_type.is_high_risk())  # True (VHRT est haut risque)
print(contract_type.is_pvp())  # True (contient 'T' = Tactical)
print(contract_type.get_reward_int())  # 50000


# ===== ORGANIZATION MODEL =====
from models import Organization

# Créer une org
org = Organization(
    sid="TEORG",
    name="Test Organization",
    tag="TE",
    member_count=150,
)

# Utiliser les propriétés
print(org.is_large())  # True (> 100 membres)
print(org.rsi_url())  # https://robertsspaceindustries.com/orgs/TEORG


# ===== AVEC LES CONTROLLERS =====
from controllers import AppController

app = AppController()

# Scanner : chercher des cibles sous forme de modèles
targets = app.scanner.search_targets_as_models("JOHN")
for target in targets:
    print(f"{target.pseudo} - {target.alignment}")

# Logger : charger un dossier sous forme de modèle
target = app.logger.load_target_as_model("JOHNDOE")
if target:
    print(f"Loaded: {target.pseudo}")
    target.add_win()
    # Sauvegarder les modifications...

# Contract : récupérer les contrats sous forme de modèles
active = app.contract.get_active_contracts_as_models()
for contract in active:
    print(f"Contract: {contract.target} (Priority: {contract.priority})")

closed = app.contract.get_closed_contracts_as_models()
for contract in closed:
    print(f"Completed: {contract.target} - Reward: {contract.get_reward_int()} aUEC")


# ===== AVANTAGES DES MODÈLES =====
# 1. Type-safe : les propriétés sont explicites
# 2. Logique métier encapsulée : méthodes utiles comme is_threat(), is_large(), etc.
# 3. Conversion facile : to_dict(), to_tuple(), from_db_row()
# 4. Représentation claire : __repr__() pour debug
