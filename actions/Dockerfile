# Utilisation de l'image rasa-sdk version 3.5.1 pour les actions personnalisées
FROM rasa/rasa-sdk:3.5.1

# Dossier de travail dans le conteneur
WORKDIR /app

# Copie de tous les fichiers locaux dans le conteneur
COPY . /app

# Installation des dépendances Python
RUN pip install -r requirements.txt

# Commande pour démarrer le serveur des actions personnalisées
CMD ["python", "-m", "rasa_sdk", "--port", "5055"]

