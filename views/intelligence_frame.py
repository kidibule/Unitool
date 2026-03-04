import customtkinter as ctk
import json
import time, threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from drake_ui.engine import DrakeConfig, DrakeButton, DrakeTerminal, DrakePopup, DrakeEntry


class IntelligenceFrame(ctk.CTkFrame):

    def __init__(self, parent, controller):

        super().__init__(parent, fg_color="transparent")

        self.controller = controller

        self.bot_driver = None

        self.last_scanned_data = None

        # --- TABS SETUP (Style Drake) ---

        self.tabview = ctk.CTkTabview(
            self,
            segmented_button_selected_color=DrakeConfig.ACCENT_PRIMARY,
            segmented_button_selected_hover_color=DrakeConfig.ACCENT_HOVER,
            segmented_button_unselected_color=DrakeConfig.BG_PANEL,
        )

        self.tabview.pack(padx=DrakeConfig.PADDING, pady=5, fill="both", expand=True)

        self.tab_player = self.tabview.add("TRACK PLAYER")

        self.tab_org = self.tabview.add("TRACK ORG")

        self.setup_player_tab()

        self.setup_org_tab()

        # Console de logs système — local terminal removed to avoid duplicates
        try:
            if hasattr(self.controller, "log"):
                self.controller.log("UPLINK STATUS: CONNECTED", source="INTEL")
        except Exception:
            pass

    def _log(self, message):
        """Forward intelligence logs to the central controller logger (no local terminal)."""
        try:
            if hasattr(self.controller, "log"):
                self.controller.log(message, source="INTEL")
        except Exception:
            pass

    def update_bot_status(self, status: str):
        """Update the visible bot status label in the player tab."""
        try:
            color = DrakeConfig.ACCENT_PRIMARY
            if status.startswith("ERROR") or status.startswith("DRIVER ERROR"):
                color = DrakeConfig.ACCENT_ERROR
            elif status.startswith("RUNNING"):
                color = "#ffd24d"
            elif status.startswith("IDLE"):
                color = DrakeConfig.TEXT_SECONDARY
            # Ensure label exists
            if hasattr(self, "bot_status_label"):
                self.bot_status_label.configure(text=f"BOT: {status}", text_color=color)
        except Exception:
            pass

    def setup_player_tab(self):

        ctk.CTkLabel(
            self.tab_player,
            text="TARGET ACQUISITION",
            font=("Orbitron", 16, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=5)

        # Small bot status label (shows CONNECTED / RUNNING / IDLE / ERROR)
        self.bot_status_label = ctk.CTkLabel(
            self.tab_player,
            text="BOT: IDLE",
            font=("Consolas", 10),
            text_color=DrakeConfig.TEXT_SECONDARY,
        )
        self.bot_status_label.pack(pady=(0, 8))

        self.ent_p = DrakeEntry(
            self.tab_player,
            placeholder_text="HANDLE...",
            width=300,
            fg_color=DrakeConfig.BG_PANEL,
            border_color=DrakeConfig.ACCENT_PRIMARY,
        )

        self.ent_p.pack(pady=5)

        btn_f = ctk.CTkFrame(self.tab_player, fg_color="transparent")

        btn_f.pack(pady=5)

        self.btn_scan_p = DrakeButton(
            btn_f, text="SCANNER", width=100, command=lambda: self.start_work("player")
        )

        self.btn_scan_p.pack(side="left", padx=5)

        self.btn_save_db = DrakeButton(
            btn_f,
            text="SAVE CONTACT",
            width=150,
            fg_color="#333",
            state="disabled",
            command=self.save_to_unitool,
        )

        self.btn_save_db.pack(side="left", padx=5)

        # Panel d'affichage des résultats

        self.info_f = ctk.CTkFrame(
            self.tab_player,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_width=1,
            border_color=DrakeConfig.ACCENT_PRIMARY,
        )

        self.info_f.pack(pady=10, padx=20, fill="x")

        self.res_nom = self.create_row(self.info_f, "DISPLAY NAME :")

        self.res_orga = self.create_row(self.info_f, "ORGANIZATION :")

        self.res_affiliates = self.create_row(self.info_f, "AFFILIATIONS :")

        self.res_date = self.create_row(self.info_f, "ENLISTED :")

        self.res_lang = self.create_row(self.info_f, "LANGUAGE :")

        # Rendre le nom de l'organisation cliquable

        self.res_orga.bind("<Double-1>", self.quick_jump_to_org)

        self.res_orga.configure(cursor="hand2")

    def create_row(self, parent, label):

        r = ctk.CTkFrame(parent, fg_color="transparent")

        r.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(
            r,
            text=label,
            font=DrakeConfig.FONT_UI,
            width=150,
            anchor="w",
            text_color=DrakeConfig.TEXT_SECONDARY,
        ).pack(side="left")

        val = ctk.CTkLabel(
            r,
            text="---",
            font=DrakeConfig.FONT_LOGS,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        )

        val.pack(side="left")

        return val

    def setup_org_tab(self):

        ctk.CTkLabel(
            self.tab_org,
            text="ORGANIZATION MAPPING",
            font=("Orbitron", 16, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=5)

        self.ent_o = DrakeEntry(
            self.tab_org,
            placeholder_text="SID...",
            width=200,
            fg_color=DrakeConfig.BG_PANEL,
            border_color=DrakeConfig.ACCENT_PRIMARY,
        )

        self.ent_o.pack(pady=5)

        btns_org = ctk.CTkFrame(self.tab_org, fg_color="transparent")

        btns_org.pack(pady=5)

        DrakeButton(
            btns_org, text="EXTRAIRE MEMBRES", command=lambda: self.start_work("org")
        ).pack(side="left", padx=5)

        self.btn_save_org_db = DrakeButton(
                btns_org, 
                text="SAVE ORGANIZATION", 
                width=180, 
                fg_color="#333", 
                state="disabled", # Désactivé par défaut
                command=self.save_org_to_unitool
            )
        self.btn_save_org_db.pack(side="left", padx=5)
        
        self.btn_save_org = DrakeButton(
            btns_org, text="EXPORTER CSV", fg_color="#333", command=self.save_org_to_csv
        )

        self.btn_save_org.pack(side="left", padx=5)

        # TERMINAL 1 : La liste des membres

        self.member_list = DrakeTerminal(
            self.tab_org, height=180, border_color=DrakeConfig.ACCENT_PRIMARY
        )

        self.member_list.pack(padx=20, pady=(10, 5), fill="both", expand=True)

        self.member_list.bind("<Button-1>", self.preview_member_data)

        self.member_list.bind("<Double-Button-1>", self.get_member_details)

        # TERMINAL 2 : Le panneau de preview (Détails DB)

        self.details_box = DrakeTerminal(
            self.tab_org, height=100, border_color=DrakeConfig.ACCENT_PRIMARY
        )

        self.details_box.pack(padx=20, pady=5, fill="x")

    def start_work(self, mode):

        t = self.ent_p.get() if mode == "player" else self.ent_o.get()

        if not t:

            return

        threading.Thread(target=self.run_bot, args=(mode, t), daemon=True).start()

    def init_driver(self):

        try:

            if not self.bot_driver:

                opts = Options()

                opts.add_argument("--headless=new")

                opts.add_argument("--window-size=1920,1080")

                opts.add_argument(
                    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )

                self.bot_driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()), options=opts
                )

            # Driver ready
            try:
                self.update_bot_status("DRIVER READY")
            except Exception:
                pass

            return True


        except Exception as e:

            self._log(f"driver error: {e}")
            try:
                self.update_bot_status("DRIVER ERROR")
            except Exception:
                pass

            return False

    def clean_player_info(self):
        """Réinitialise l'affichage des informations du joueur"""

        self.res_nom.configure(text="---")

        self.res_orga.configure(text="---")

        self.res_date.configure(text="---")

        self.res_lang.configure(text="---")

        if hasattr(self, "res_affiliates"):

            self.res_affiliates.configure(text="---")

        # Reset du bouton de sauvegarde

        self.btn_save_db.configure(
            state="disabled", fg_color="#333", text="SAVE CONTACT"
        )

        self.last_scanned_data = None

    def clean_org_info(self):
        """Réinitialise l'affichage des membres et des détails d'organisation"""

        self.member_list.delete("1.0", "end")

        self.member_list.log("CLEANING BUFFER...")  # Optionnel : petit message de reset

        self.details_box.delete("1.0", "end")

        self._log("ORGANIZATION DATA PURGED")

    def run_bot(self, mode, target):

        self._log(f"uplink initiated: {target}")
        try:
            self.update_bot_status(f"RUNNING: {target}")
        except Exception:
            pass

        try:

            if self.init_driver():

                if mode == "player":

                    # --- NETTOYAGE DES INFOS PRÉCÉDENTES ---

                    self.clean_player_info()

                    # Initialisation du dictionnaire de données

                    d = {
                        "Handle": target,
                        "OrgaNom": "NONE",
                        "SID": "N/A",
                        "Rang": "N/A",
                        "Date": "N/A",
                        "Language": "N/A",
                    }

                    # --- ÉTAPE 1 : PAGE PROFIL ---

                    self._log(f"scanning profile: {target}...")

                    self.bot_driver.get(
                        f"https://robertsspaceindustries.com/citizens/{target}"
                    )

                    time.sleep(4)

                    try:

                        # Utilisation de la méthode body.text (très stable)

                        body_text = self.bot_driver.find_element(
                            By.TAG_NAME, "body"
                        ).text

                        lines = [l.strip() for l in body_text.split("\n") if l.strip()]

                        for i, line in enumerate(lines):

                            if "Enlisted" in line and i + 1 < len(lines):

                                d["Date"] = self.convert_date_to_be(lines[i + 1])

                            elif "Fluency" in line and i + 1 < len(lines):

                                d["Language"] = lines[i + 1]

                    except Exception as e:

                        self._log("profile parse warning")

                    # --- ÉTAPE 2 : PAGE ORGANIZATIONS (Cible: Le Syndicat) ---

                    # --- ÉTAPE 2 : PAGE ORGANIZATIONS (Méthode de recherche par liens) ---

                    self._log(f"intercepting organization data...")

                    self.bot_driver.get(
                        f"https://robertsspaceindustries.com/citizens/{target}/organizations"
                    )

                    time.sleep(5)  # On laisse un peu plus de temps

                    try:

                        # On récupère tous les liens qui contiennent "/orgs/"

                        # Le premier lien trouvé dans la page est presque toujours l'organisation principale

                        org_links = self.bot_driver.find_elements(
                            By.XPATH, "//a[contains(@href, '/orgs/')]"
                        )

                        found = False

                        for link in org_links:

                            name_text = link.text.strip()

                            # On vérifie que le lien n'est pas une icône vide ou un doublon du SID

                            if name_text and len(name_text) > 1:

                                d["OrgaNom"] = name_text.split("/")[0].strip()

                                d["SID"] = (
                                    link.get_attribute("href").split("/")[-1].upper()
                                )

                                found = True

                                break  # On prend la première orga trouvée (la Main)

                        # Si on a trouvé l'orga, on essaie de choper le rang à côté

                        if found:

                            try:

                                # Correction : utiliser CSS_SELECTOR (By.CSS_COLOR n'existe pas)

                                d["Rang"] = self.bot_driver.find_element(
                                    By.CSS_SELECTOR, ".rank-name"
                                ).text.strip()

                            except:

                                pass

                        else:

                            d["OrgaNom"] = "NONE / PRIVATE"

                    except Exception as e:

                        self._log("org scan failed")

                        d["OrgaNom"] = "ERROR"

                    # --- MISE À JOUR UI ---

                    self.res_nom.configure(text=target.upper())

                    self.res_orga.configure(text=d["OrgaNom"])  # Affiche "Le Syndicat"

                    self.res_date.configure(text=d["Date"])

                    self.res_lang.configure(text=d["Language"])

                    # On met à jour les affiliations ou le rang si tu as ajouté la ligne

                    if hasattr(self, "res_affiliates"):

                        self.res_affiliates.configure(text=d["Rang"])

                    self.last_scanned_data = d

                    self.btn_save_db.configure(
                        state="normal", fg_color=DrakeConfig.ACCENT_PRIMARY
                    )

                    self._log(f"intel acquired: {target}")

                elif mode == "org":

                    self.clean_org_info()

                    sid = target.strip().upper()

                    self.bot_driver.get(
                        f"https://robertsspaceindustries.com/orgs/{sid}/members"
                    )

                    time.sleep(5)

                    self.bot_driver.execute_script("window.scrollTo(0, 1000);")

                    time.sleep(2)

                    members = self.bot_driver.find_elements(
                        By.CSS_SELECTOR, "li.m-member, .member-item"
                    )

                    if members:

                        self.member_list.delete("1.0", "end")

                        self.member_list.insert(
                            "end", f"{'HANDLE':<25} | {'RANK':<20}\n{'-'*50}\n"
                        )

                        v_count, r_count = 0, 0

                        for m in members:

                            try:

                                try:

                                    h = m.find_element(
                                        By.CSS_SELECTOR, ".nick"
                                    ).text.strip()

                                except:

                                    h = ""

                                if not h:

                                    h, r_count = "[REDACTED]", r_count + 1

                                else:

                                    v_count += 1

                                try:

                                    r = m.find_element(
                                        By.CSS_SELECTOR, ".rank"
                                    ).text.strip()

                                except:

                                    r = "MEMBER"

                                self.member_list.insert("end", f"{h:<25} | {r:<20}\n")

                            except:

                                r_count += 1

                        self.member_list.insert(
                            "end",
                            f"{'-'*50}\nTOTAL: {v_count+r_count} | VISIBLE: {v_count} | REDACTED: {r_count}\n",
                        )

                        self._log(f"mapping complete: {sid}")
                        self.btn_save_org_db.configure(state="normal", fg_color=DrakeConfig.ACCENT_PRIMARY)

                    else:

                        self._log("error: no public roster found")

        except Exception as e:

            self._log(f"uplink failure: {str(e)[:30]}")
        finally:
            try:
                self.update_bot_status("IDLE")
            except Exception:
                pass

    def quick_jump_to_org(self, event):
        """Action au double-clic sur le nom d'orga"""

        if self.last_scanned_data and self.last_scanned_data["SID"] != "N/A":

            sid = self.last_scanned_data["SID"]

            self.tabview.set("TRACK ORG")

            self.ent_o.delete(0, "end")

            self.ent_o.insert(0, sid)

            self.start_work("org")

    def convert_date_to_be(self, rsi_date):

        try:

            clean = rsi_date.replace(",", "").strip()

            return datetime.strptime(clean, "%b %d %Y").strftime("%d/%m/%Y")

        except:

            return rsi_date

    def get_member_details(self, event):
        """Lancement du scan complet au double-clic"""

        try:

            line_index = self.member_list.index("current").split(".")[0]

            line_content = self.member_list.get(f"{line_index}.0", f"{line_index}.end")

            if "|" in line_content and "HANDLE" not in line_content:

                h = line_content.split("|")[0].strip()

                if "[REDACTED]" not in h:

                    self.details_box.delete("1.0", "end")

                    self.details_box.log(f"INITIATING FULL SCAN FOR {h}...")

                    self.ent_p.delete(0, "end")

                    self.ent_p.insert(0, h)

                    self.tabview.set("TRACK PLAYER")

                    self.start_work("player")

        except:

            pass

    def save_to_unitool(self):

        if not self.last_scanned_data:
            return

        try:
            # Normalize handle
            handle = (
                self.last_scanned_data.get("Handle")
                or self.last_scanned_data.get("handle")
                or ""
            )
            handle = str(handle).strip().upper()
            if not handle:
                raise ValueError("Missing handle in scanned data")

            # Check existing entry
            existing = self.controller.intelligence.get_target_snapshot(handle)

            # Prepare scanned values for comparison
            scanned_org = (self.last_scanned_data.get("OrgaNom") or "").strip()
            scanned_sid = (self.last_scanned_data.get("SID") or "").strip().upper()
            scanned_rank = (self.last_scanned_data.get("Rang") or "").strip()
            scanned_date = (self.last_scanned_data.get("Date") or "").strip()
            scanned_lang = (self.last_scanned_data.get("Language") or "").strip()
            scanned_aff = (self.last_scanned_data.get("Affiliates") or "").strip()

            if existing:
                row = existing
                same = (
                    ((str(row[0] or "")).upper() == scanned_org.upper()) and
                    ((str(row[1] or "")).upper() == scanned_sid.upper()) and
                    ((str(row[2] or "")).upper() == scanned_rank.upper()) and
                    ((str(row[3] or "")).upper() == scanned_date.upper()) and
                    ((str(row[4] or "")).upper() == scanned_lang.upper()) and
                    ((str(row[5] or "")).upper() == scanned_aff.upper())
                )
                if same:
                    DrakePopup.info("SYSTEMS", f"Aucune modification détectée pour {handle}. Sauvegarde évitée.", parent=self)
                    self._log(f"save skipped (no change): {handle}")
                    # disable button to avoid re-save
                    try:
                        self.btn_save_db.configure(state="disabled", fg_color="#333", text="ENREGISTRER CONTACT")
                    except Exception:
                        pass
                    return

                # Build a human-readable diff of changes
                diffs = []
                if (str(row[0] or "")).upper() != scanned_org.upper():
                    diffs.append(f"ORGANIZATION: {row[0] or 'None'}  ->  {scanned_org}")
                if (str(row[1] or "")).upper() != scanned_sid.upper():
                    diffs.append(f"SID: {row[1] or 'None'}  ->  {scanned_sid}")
                if (str(row[2] or "")).upper() != scanned_rank.upper():
                    diffs.append(f"RANK: {row[2] or 'None'}  ->  {scanned_rank}")
                if (str(row[3] or "")).upper() != scanned_date.upper():
                    diffs.append(f"ENLISTED: {row[3] or 'None'}  ->  {scanned_date}")
                if (str(row[4] or "")).upper() != scanned_lang.upper():
                    diffs.append(f"LANGUAGE: {row[4] or 'None'}  ->  {scanned_lang}")
                if (str(row[5] or "")).upper() != scanned_aff.upper():
                    diffs.append(f"AFFILIATES: {row[5] or 'None'}  ->  {scanned_aff}")

                diff_text = "\n".join(diffs)
                prompt = f"Le dossier {handle} existe déjà. Changements détectés:\n\n{diff_text}\n\nMettre à jour avec ces nouvelles valeurs ?"
                confirm = DrakePopup.yesno("CHANGEMENTS DÉTECTÉS", prompt, parent=self)
                if not confirm:
                    return

            # Proceed to upsert
            # Ensure the data uses the handle uppercase as in DB
            self.last_scanned_data["Handle"] = handle
            self.controller.upsert_target_intel(self.last_scanned_data)

            self.btn_save_db.configure(
                fg_color="#2ecc71", text="ARCHIVÉ ✓", state="disabled"
            )

            self._log(f"dossier archived in database: {handle}")

        except Exception as e:
            DrakePopup.error("ERREUR", f"Erreur lors de l'archivage : {e}", parent=self)
            self._log(f"error saving to db: {e}")

    def save_org_to_csv(self):

        sid = self.ent_o.get().strip().upper()

        if not sid:

            return

        with open(f"ORG_{sid}.csv", "w", encoding="utf-8") as f:

            f.write(self.member_list.get("1.0", "end"))

        self._log(f"export complete: org_{sid}.csv")

    def preview_member_data(self, event):
        """Affiche les données locales au simple clic"""

        try:

            # Récupérer le handle sur la ligne cliquée

            line_index = self.member_list.index(f"@{event.x},{event.y}").split(".")[0]

            line_content = self.member_list.get(f"{line_index}.0", f"{line_index}.end")

            if "|" in line_content and "HANDLE" not in line_content:

                handle = line_content.split("|")[0].strip()

                if "[REDACTED]" in handle:

                    return

                # Interroger la DB via ton controller

                # (J'assume que ton controller a une méthode pour chercher un profil)

                local_data = self.controller.get_target_by_handle(handle)

                self.details_box.delete("1.0", "end")

                if local_data:

                    self.details_box.log(f"--- LOCAL DOSSIER: {handle} ---")

                    # On affiche les infos que tu as stockées (ex: Orga, Date, Notes...)

                    info_str = f"ORG: {local_data.get('OrgaNom', 'Unknown')} | SID: {local_data.get('SID', 'N/A')}\n"

                    info_str += f"ENLISTED: {local_data.get('Date', 'N/A')} | LANG: {local_data.get('Language', 'N/A')}"

                    self.details_box.insert("end", info_str)

                else:

                    self.details_box.log(
                        f"NO LOCAL DATA FOR {handle}. DOUBLE-CLICK TO SCAN."
                    )

        except Exception as e:

            pass

    def save_org_to_unitool(self):
        """Synchronise les données scannées avec le OrgController."""
        import json
        from datetime import datetime
        
        sid = self.ent_o.get().strip().upper()
        if not sid or len(sid) < 2: # Sécurité : on n'enregistre pas de SID vide ou trop court
            return

        # 1. Analyse du terminal
        raw_lines = self.member_list.get("1.0", "end").splitlines()
        visible_members = []
        redacted_count = 0

        for line in raw_lines:
            # On ignore les lignes de déco, les titres et les lignes vides
            if "|" in line and "HANDLE" not in line and "---" not in line and "TOTAL" not in line:
                parts = line.split("|")
                handle = parts[0].strip()
                rank = parts[1].strip() if len(parts) > 1 else "MEMBER"
                
                if "[REDACTED]" in handle:
                    redacted_count += 1
                elif handle and handle != "HANDLE": # Évite d'ajouter les en-têtes
                    visible_members.append({"h": handle, "r": rank})

        # 2. Préparation des données
        total_members = len(visible_members) + redacted_count
        data_payload = {
            "member_count": total_members,
            "visible_members": json.dumps(visible_members),
            "redacted_members": f"REDACTED_COUNT:{redacted_count}",
            "updated_at": datetime.now().strftime("%d/%m/%Y")
        }

        try:
            action_text = self.controller.intelligence.save_org_snapshot(sid, sid, data_payload)

            # 4. Feedback
            self.btn_save_org_db.configure(
                fg_color="#2ecc71", 
                text=f"ORG {action_text} ✓", 
                state="disabled"
            )
            main_win = self.winfo_toplevel()
            main_win.attributes("-topmost", True)
            
            self._log(f"UPLINK SUCCESS: {sid} synchronization complete.")
            DrakePopup.info("SYSTEMS", f"Dossier {sid} synchronisé.\nMembres: {total_members}", parent=main_win)

        except Exception as e:
            self._log(f"Controller Error: {e}")
            DrakePopup.error("SYNC FAILURE", f"Détails : {e}")