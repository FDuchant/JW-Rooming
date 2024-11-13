import logging
from logging.handlers import RotatingFileHandler
import streamlit as st
import time

# Configurer le fichier de log
log_filename = "app.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    handlers=[
        RotatingFileHandler(log_filename, maxBytes=1000000, backupCount=3),  # Gestionnaire de log pour fichier
    ]
)

# Ajouter un gestionnaire pour afficher les logs dans la console et sur Streamlit
class StreamlitHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        self.logs = []

    def emit(self, record):
        # Ajoute le message log à une liste
        msg = self.format(record)
        self.logs.append(msg)

    def get_logs(self):
        # Retourner les logs accumulés
        return "\n".join(self.logs)

# Créer une instance de ce gestionnaire personnalisé
streamlit_handler = StreamlitHandler()
streamlit_handler.setLevel(logging.INFO)

# Ajouter un format de log pour la sortie Streamlit
formatter = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")
streamlit_handler.setFormatter(formatter)

# Ajouter ce gestionnaire au logger
logging.getLogger().addHandler(streamlit_handler)

# Début de l'application Streamlit
st.title("Application avec logs en direct")

# Un conteneur Streamlit pour afficher les logs
log_container = st.empty()

# Fonction simulant des logs
def generate_logs():
    for i in range(10):
        logging.info(f"Processus en cours... étape {i+1}")
        time.sleep(1)  # Simule un traitement en cours
        # Affiche les logs mis à jour dans Streamlit
        log_container.text_area("Logs en direct", streamlit_handler.get_logs(), height=200)

# Bouton pour démarrer la génération de logs
if st.button("Démarrer les logs"):
    generate_logs()

if st.button("Gestion des erreurs"):
    logging.warning(f"Erreur en cours d'analyse")
    log_container.text_area("Logs en direct", streamlit_handler.get_logs(), height=200)
    logging.error(f"Confirmation d'erreur détectée")
    log_container.text_area("Logs en direct", streamlit_handler.get_logs(), height=200)
