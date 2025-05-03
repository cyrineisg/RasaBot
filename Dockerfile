# Utilise l’image officielle Rasa avec la bonne version
FROM rasa/rasa:3.5.11

# Définit le répertoire de travail
WORKDIR /app

# Copie tout le contenu du projet dans l'image
COPY . /app

# Installe les dépendances Python si le fichier existe
RUN [ -f requirements.txt ] && pip install --no-cache-dir -r requirements.txt || echo "Pas de requirements.txt"

# Commande pour démarrer le serveur Rasa avec l’API et le CORS activé
CMD ["run", "--enable-api", "--cors", "*", "--debug"]

