"""Exemple d'utilisation des sub-controllers.

Ce fichier montre comment mettre à jour les vues pour utiliser les
sub-controllers au lieu d'accéder directement à self.controller.db.
"""

# ===== EXEMPLE 1 : SCANNER (ScannerFrame) =====
# AVANT (maintenant déprécié) :
# rows = self.controller.db.query("SELECT * FROM targets WHERE pseudo LIKE ?", (f'%{q}%',))

# APRÈS (recommandé) :
# rows = self.controller.scanner.search_targets(q)


# ===== EXEMPLE 2 : LOGGER (LoggerFrame) =====
# AVANT :
# self.controller.db.commit(sql, params)

# APRÈS :
# self.controller.logger.save_target(
#     pseudo="PLAYERNAME",
#     org="ORGA_NAME",
#     sid="SID",
#     org_rank="RANK",
#     language="FR",
#     alignment="NEUTRE",
#     ship="F7C-M",
#     pvp_lvl="VETERAN",
#     activity="TRADER",
#     notes="Notes here...",
#     threat="MEDIUM",
#     wins=5,
#     losses=2
# )


# ===== EXEMPLE 3 : CONTRATS (ContractFrame) =====
# AVANT :
# self.controller.db.cursor.execute("INSERT INTO contracts ...", (params,))

# APRÈS :
# self.controller.contract.add_contract(
#     target="PSEUDO_CIBLE",
#     client="CLIENT_ID",
#     reward="5000",
#     priority="HIGH",
#     contract_type="VHRT"
# )

# Récupérer les contrats actifs :
# active = self.controller.contract.get_active_contracts()

# Fermer un contrat :
# self.controller.contract.complete_contract(contract_id=1, target="PSEUDO")


# ===== EXEMPLE 4 : INTELLIGENCE (IntelligenceFrame) =====
# AVANT :
# self.controller.db.upsert_target_intel(data)

# APRÈS :
# self.controller.intelligence.save_player_intel(data)

# Récupérer les infos locales :
# intel = self.controller.intelligence.get_player_intel(handle="PLAYERNAME")

# Mettre à jour après scraping :
# self.controller.intelligence.update_player_intel(
#     pseudo="PLAYERNAME",
#     org="ORGA",
#     sid="SID",
#     org_rank="RANK"
# )


# ===== MIGRATION GRADUELLE =====
# Les vues peuvent continuer à utiliser self.controller.db et self.controller.cursor
# pour les opérations brutes, mais c'est recommandé d'utiliser les sub-controllers
# pour les opérations courantes, car c'est plus lisible et maintenable.

# Les sub-controllers encapsulent la logique métier et simplifient les vues.
