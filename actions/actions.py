import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Dict, List, Text
from collections import Counter
from bs4 import BeautifulSoup


API_URL = "https://timserver.northeurope.cloudapp.azure.com/QalitasWebApi/api/Audits"
AUTH_TOKEN = "ammi4vp8rvNiGxLq51QAgPpDdXK0uF5GPRRK5OX6BuiO-neTsXXetmY0LDUI6iBHpQODBFod8mAkGOLey-Rb1BgwRqXMvP9LkrVWSds4BtYajnhTMOsHkYGuv-1TpEJbZwSdhZPrnueEtrleoEix89AXwoyO7cfof15nQAcSS46aNYHVzjOiKYIbtukE9v9BEo78VB6WbYLgzABbSfYGRX_-8R_lKnXVD52h-EbuEgEig0y22WPb86vmA2rQWSy1kDPV-cbdFgrugYL43RAhxNpAx9cNRdmB8gnG5Jhr5T8_r1z0ooooLkBhSqA_aenBGuwQkfBdUUDhLPmYMIA016WlfVBlVXzrUMY0JBm1UJrjKQhce9e93UBzp-NO_NSEz1gEmqY7_I-t39pIRa2ajL4P_cnqi_7TTF2B688WKc6que5XL-aZQ5coPbz3WmEHGulYW7n-NRmg0EzIPzXTJGhokxgnqgrT8LyKJ-rdCRs"

class ActionGetAllAudits(Action):
    def name(self) -> str:
        return "action_get_all_audits"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.get(API_URL, headers=headers)
        if response.status_code == 200:
            audits = response.json()
            message = "Voici les audits disponibles :\n"
            for index, audit in enumerate(audits, start=1):
                process_list = audit.get("auditProcesses", [])
                designations = [proc.get("processDesignation", "N/A") for proc in process_list]
                designation_str = ", ".join(designations)
                message += f"{index}. Référence: {audit['reference']} | Année: {audit['year']} | Processus: {designation_str}\n"
            message += f"\nNombre total d'audits : {len(audits)}"
            dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(text="Je n'ai pas pu récupérer les audits.")
        return []



class ActionGetAuditInfo(Action):
    def name(self) -> str:
        return "action_get_audit_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        # Récupérer la référence de l'audit de l'utilisateur
        audit_ref = next(tracker.get_latest_entity_values("audit_reference"), None)

        if not audit_ref:
            dispatcher.utter_message(text=f"Aucun audit trouvé avec la référence '{audit_ref}'. Veuillez vérifier que la référence est correcte.")
            return []

        # Appel à l'API pour récupérer tous les audits
        response = requests.get(API_URL, headers=headers)
        if response.status_code == 200:
            audits = response.json()
            # Rechercher l'audit qui correspond à la référence donnée
            audit = self.get_audit_by_reference(audits, audit_ref)

            if audit:
                # Extraire les informations de l'audit
                process_list = audit.get("auditProcesses", [])
                designations = [proc.get("processDesignation", "N/A") for proc in process_list]
                designation_str = ", ".join(designations)
                message = (
                    f"Audit {audit['reference']} :\n"
                    f"Année : {audit['year']}\n"
                    f"Processus : {designation_str}\n"
                    f"Statut : {audit.get('stateStr', 'N/A')}\n"
                    f"Nature de l'audit : {audit.get('auditNatureStr', 'N/A')}"
                )

                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text="Aucun audit trouvé avec cette référence.")
        else:
            dispatcher.utter_message(text="Erreur lors de la récupération des données depuis l'API.")
        
        return []

    def get_audit_by_reference(self, audits, reference):
        # Filtrer les audits pour trouver celui qui correspond à la référence
        for audit in audits:
            if audit['reference'] == reference:
                return audit
        return None
    

class ActionFilterAuditsByYear(Action):
    def name(self) -> str:
        return "action_filter_audits_by_year"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        start_year = next(tracker.get_latest_entity_values("start_year"), None)
        end_year = next(tracker.get_latest_entity_values("end_year"), None)

        if not start_year or not end_year:
            dispatcher.utter_message(text="Merci de préciser les deux années pour filtrer les audits.")
            return []

        try:
            start_year = int(start_year)
            end_year = int(end_year)
        except ValueError:
            dispatcher.utter_message(text="Les années doivent être des nombres.")
            return []

        if start_year > end_year:
            dispatcher.utter_message(text="L'année de début doit être inférieure ou égale à l'année de fin.")
            return []

        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.get(API_URL, headers=headers)
        if response.status_code == 200:
            audits = response.json()
            filtered_audits = [
                audit for audit in audits
                if start_year <= audit.get("year", 0) <= end_year
            ]

            if filtered_audits:
                message = f"Voici les audits entre {start_year} et {end_year} :\n"
                
                # --- Comptage des stateStr et auditNatureStr ---
                state_counter = Counter()
                nature_counter = Counter()

                for audit in filtered_audits:
                    message += f"- {audit.get('reference', 'Référence inconnue')} (Année : {audit.get('year', 'Inconnue')})\n"
                    state_counter[audit.get('stateStr', 'Inconnu')] += 1
                    nature_counter[audit.get('auditNatureStr', 'Inconnu')] += 1

                # --- Affichage des statistiques ---
                message += "\nRésumé par état (stateStr) :\n"
                for state, count in state_counter.items():
                    message += f"  - {state} : {count}\n"

                message += "\nRésumé par nature d'audit (auditNatureStr) :\n"
                for nature, count in nature_counter.items():
                    message += f"  - {nature} : {count}\n"

                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text=f"Aucun audit trouvé entre {start_year} et {end_year}.")
        else:
            dispatcher.utter_message(text="Erreur lors de la récupération des données depuis l'API.")

        return []
    



class ActionResumeAuditsByYear(Action):
    def name(self) -> Text:
        return "action_resume_audits_by_year"

    def clean_html(self, raw_html: str) -> str:
        """Nettoie le texte HTML pour l'affichage propre."""
        if not raw_html:
            return ""
        soup = BeautifulSoup(raw_html, "html.parser")
        return soup.get_text(separator="\n").strip()

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        start_year = next(tracker.get_latest_entity_values("start_year"), None)
        end_year = next(tracker.get_latest_entity_values("end_year"), None)

        if not start_year or not end_year:
            dispatcher.utter_message(text="Merci de préciser les deux années pour obtenir le résumé des audits.")
            return []

        try:
            start_year = int(start_year)
            end_year = int(end_year)
        except ValueError:
            dispatcher.utter_message(text="Les années doivent être des nombres.")
            return []

        if start_year > end_year:
            dispatcher.utter_message(text="L'année de début doit être inférieure ou égale à l'année de fin.")
            return []

        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(API_URL, headers=headers)
            response.raise_for_status()
            audits = response.json()
        except requests.RequestException:
            dispatcher.utter_message(text="Erreur lors de la récupération des données depuis l'API.")
            return []
        except ValueError:
            dispatcher.utter_message(text="Erreur lors de la lecture de la réponse JSON.")
            return []

        if not isinstance(audits, list):
            audits = []

        filtered_audits = [
            audit for audit in audits
            if isinstance(audit, dict) and start_year <= audit.get("year", 0) <= end_year
        ]

        if not filtered_audits:
            dispatcher.utter_message(text=f"Aucun audit trouvé entre {start_year} et {end_year}.")
            return []

        strengths = set()
        weaknesses = set()
        recommendations = set()
        total_non_conformities = 0

        for audit in filtered_audits:
            processes = audit.get("auditProcesses", [])
            if isinstance(processes, list):
                for process in processes:
                    if isinstance(process, dict):
                        strength = self.clean_html(process.get("strength"))
                        weakness = self.clean_html(process.get("weakness"))
                        recommendation = self.clean_html(process.get("recommendation"))

                        if strength:
                            strengths.add(strength)
                        if weakness:
                            weaknesses.add(weakness)
                        if recommendation:
                            recommendations.add(recommendation)

            non_conformities = audit.get("nonConformityList", [])
            if isinstance(non_conformities, list):
                total_non_conformities += len(non_conformities)

        strengths.discard("")
        weaknesses.discard("")
        recommendations.discard("")

        message = f"📄 **Résumé des audits entre {start_year} et {end_year}** 📄\n\n"

        if strengths:
            message += "✅ **Points forts identifiés :**\n"
            for strength in strengths:
                message += f"- {strength}\n"
            message += "\n"

        if weaknesses:
            message += "⚠️ **Points faibles identifiés :**\n"
            for weakness in weaknesses:
                message += f"- {weakness}\n"
            message += "\n"

        if recommendations:
            message += "🛠️ **Recommandations proposées :**\n"
            for recommendation in recommendations:
                message += f"- {recommendation}\n"
            message += "\n"

        message += f"📋 **Nombre total de non-conformités :** {total_non_conformities}\n"

        dispatcher.utter_message(text=message)

        return []    