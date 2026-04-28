"""Controller pour la gestion des données de minage (signatures radar)."""

import copy
import csv
from tkinter import filedialog, messagebox


# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTES DE RÉFÉRENCE
# ──────────────────────────────────────────────────────────────────────────────

RARITY_COLORS = {
    "legendary": "#ff8c00",
    "epic":      "#9b59b6",
    "rare":      "#3498db",
    "uncommon":  "#00b894",
    "common":    "#74b9ff",
}

RARITY_LABELS = {
    "legendary": "LÉGENDAIRE",
    "epic":      "ÉPIQUE",
    "rare":      "RARE",
    "uncommon":  "PEU COMMUN",
    "common":    "COMMUN",
}

RADAR_SIGNATURES: list[dict] = [
    # ── Légendaire (max 2 rochers) ─────────────────────────────────────────
    {"name": "Quantainium", "rarity": "legendary", "sigs": [3170, 6340]},
    {"name": "Stileron",    "rarity": "legendary", "sigs": [3185, 6370]},
    {"name": "Savrilium",   "rarity": "legendary", "sigs": [3200, 6400]},
    # ── Épique (max 3 rochers) ─────────────────────────────────────────────
    {"name": "Ouratite",    "rarity": "epic",      "sigs": [3370, 6740, 10110]},
    {"name": "Riccite",     "rarity": "epic",      "sigs": [3385, 6770, 10155]},
    {"name": "Lindinium",   "rarity": "epic",      "sigs": [3400, 6800, 10200]},
    # ── Rare (max 4 rochers) ───────────────────────────────────────────────
    {"name": "Beryl",       "rarity": "rare",      "sigs": [3540, 7080, 10620, 14160]},
    {"name": "Taranite",    "rarity": "rare",      "sigs": [3555, 7110, 10665, 14220]},
    {"name": "Borase",      "rarity": "rare",      "sigs": [3570, 7140, 10710, 14280]},
    {"name": "Gold",        "rarity": "rare",      "sigs": [3585, 7170, 10755, 14340]},
    {"name": "Bexalite",    "rarity": "rare",      "sigs": [3600, 7200, 10800, 14400]},
    # ── Peu commun (max 5 rochers) ─────────────────────────────────────────
    {"name": "Laranite",    "rarity": "uncommon",  "sigs": [3825, 7650, 11475, 15300, 19125]},
    {"name": "Aslarite",    "rarity": "uncommon",  "sigs": [3840, 7680, 11520, 15360, 19200]},
    {"name": "Titanium",    "rarity": "uncommon",  "sigs": [3855, 7710, 11565, 15420, 19275]},
    {"name": "Tungsten",    "rarity": "uncommon",  "sigs": [3870, 7740, 11610, 15480, 19350]},
    {"name": "Agricium",    "rarity": "uncommon",  "sigs": [3885, 7770, 11655, 15540, 19425]},
    {"name": "Torite",      "rarity": "uncommon",  "sigs": [3900, 7800, 11700, 15600, 19500]},
    # ── Commun (max 6 rochers) ─────────────────────────────────────────────
    {"name": "Hephaestanite", "rarity": "common",  "sigs": [4180, 8360, 12540, 16720, 20900, 25080]},
    {"name": "Tin",           "rarity": "common",  "sigs": [4195, 8390, 12585, 16780, 20975, 25170]},
    {"name": "Quartz",        "rarity": "common",  "sigs": [4210, 8420, 12630, 16840, 21050, 25260]},
    {"name": "Corundum",      "rarity": "common",  "sigs": [4225, 8450, 12675, 16900, 21125, 25350]},
    {"name": "Copper",        "rarity": "common",  "sigs": [4240, 8480, 12720, 16960, 21200, 25440]},
    {"name": "Silicon",       "rarity": "common",  "sigs": [4255, 8510, 12765, 17020, 21275, 25530]},
    {"name": "Iron",          "rarity": "common",  "sigs": [4270, 8540, 12810, 17080, 21350, 25620]},
    {"name": "Aluminium",     "rarity": "common",  "sigs": [4285, 8570, 12855, 17140, 21425, 25710]},
    {"name": "Ice",           "rarity": "common",  "sigs": [4300, 8600, 12900, 17200, 21500, 25800]},
]

SPECIAL_CATEGORIES: list[dict] = [
    {
        "name":  "ROC Mineables",
        "color": "#00b894",
        "sigs":  [4000, 8000, 12000, 16000, 20000, 24000, 28000],
    },
    {
        "name":  "FPS Mineables",
        "color": "#3498db",
        "sigs":  [3000, 6000, 9000, 12000, 15000, 18000, 21000, 24000, 27000, 30000],
    },
    {
        "name":  "Salvage",
        "color": "#aaaaaa",
        "sigs":  [2000, 4000, 6000, 8000, 10000, 12000, 14000, 16000,
                  18000, 20000, 22000, 24000, 26000, 28000, 30000],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# CONTROLLER
# ──────────────────────────────────────────────────────────────────────────────

class MiningController:
    """Gère la logique métier du minage : données, recherche et CSV I/O."""

    def __init__(self, app):
        self.app = app
        self._signatures: list[dict] = copy.deepcopy(RADAR_SIGNATURES)

    # ── Accès aux données ────────────────────────────────────────────────────

    def get_signatures(self) -> list[dict]:
        """Retourne la liste courante des signatures (défaut ou importées)."""
        return self._signatures

    def get_special_categories(self) -> list[dict]:
        """Retourne les catégories spéciales (ROC, FPS, Salvage)."""
        return SPECIAL_CATEGORIES

    # ── Recherche ────────────────────────────────────────────────────────────

    def search_signature(self, raw: str) -> list[dict]:
        """Retourne les correspondances exactes pour une valeur de signature.

        Retourne une liste de dicts :
          {"name": str, "rarity": str|None, "count": int, "sig": int, "color": str}
        """
        try:
            value = int(raw.strip().replace(" ", "").replace(".", ""))
        except ValueError:
            return []

        results = []

        for mineral in self._signatures:
            for idx, sig in enumerate(mineral["sigs"]):
                if sig == value:
                    results.append({
                        "name":   mineral["name"],
                        "rarity": mineral["rarity"],
                        "count":  idx + 1,
                        "sig":    sig,
                        "color":  RARITY_COLORS.get(mineral["rarity"], "#ffffff"),
                    })

        for cat in SPECIAL_CATEGORIES:
            for idx, sig in enumerate(cat["sigs"]):
                if sig == value:
                    results.append({
                        "name":   cat["name"],
                        "rarity": None,
                        "count":  idx + 1,
                        "sig":    sig,
                        "color":  cat["color"],
                    })

        return results

    # ── CSV I/O ──────────────────────────────────────────────────────────────

    def export_signatures_to_csv(self):
        """Exporte les signatures radar vers un fichier CSV choisi par l'utilisateur."""
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="EXPORTER LES SIGNATURES RADAR",
            initialfile="mining_signatures.csv",
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["name", "rarity", "sig_1", "sig_2", "sig_3",
                                  "sig_4", "sig_5", "sig_6"])
                for m in self._signatures:
                    row = [m["name"], m["rarity"]] + m["sigs"] + [""] * (6 - len(m["sigs"]))
                    writer.writerow(row)
            messagebox.showinfo("UNITOOL", f"Export réussi :\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def import_signatures_from_csv(self) -> list[dict] | None:
        """Importe les signatures radar depuis un fichier CSV.

        Met à jour la liste interne et retourne les nouvelles données,
        ou None si l'import a échoué ou a été annulé.
        """
        path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")],
            title="IMPORTER LES SIGNATURES RADAR",
        )
        if not path:
            return None
        try:
            new_signatures = []
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name   = row.get("name", "").strip()
                    rarity = row.get("rarity", "").strip().lower()
                    if not name or rarity not in RARITY_COLORS:
                        continue
                    sigs = []
                    for i in range(1, 7):
                        val = row.get(f"sig_{i}", "").strip()
                        if val:
                            try:
                                sigs.append(int(val))
                            except ValueError:
                                break
                    if not sigs:
                        continue
                    new_signatures.append({"name": name, "rarity": rarity, "sigs": sigs})

            if not new_signatures:
                messagebox.showwarning("Import", "Aucune donnée valide trouvée dans le fichier.")
                return None

            self._signatures = new_signatures
            messagebox.showinfo("UNITOOL", f"{len(new_signatures)} minéraux importés avec succès.")
            return self._signatures

        except Exception as e:
            messagebox.showerror("Import Error", str(e))
            return None
