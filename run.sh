#!/bin/bash

# Chemin vers le fichier de configuration
CONF_PATH="conf/conf.yml"
TMP_CONF_PATH="/tmp/conf.yaml"

# Copier le fichier de configuration dans /tmp
echo "Copie de $CONF_PATH vers $TMP_CONF_PATH..."
if cp "$CONF_PATH" "$TMP_CONF_PATH"; then
    echo "Fichier copié avec succès."
else
    echo "Erreur lors de la copie du fichier." >&2
    exit 1
fi

# Se déplacer dans le dossier server et lancer server.py
SERVER_PATH="server.py"
echo "Déplacement vers le répertoire 'server' et lancement de $SERVER_PATH..."
cd server || { echo "Impossible d'accéder au répertoire 'server'."; exit 1; }
python3 "$SERVER_PATH" &
SERVER_PID=$!

# Attendre un instant pour s'assurer que le serveur démarre
sleep 2

# Vérifier si le serveur est lancé
if ps -p "$SERVER_PID" > /dev/null; then
    echo "Le serveur est lancé avec succès (PID: $SERVER_PID)."
else
    echo "Échec du lancement du serveur." >&2
    exit 1
fi

# Se déplacer dans le dossier client et lancer client.py
CLIENT_PATH="client/client.py"
echo "Déplacement vers le répertoire 'client' et lancement de $CLIENT_PATH..."
cd ../client || { echo "Impossible d'accéder au répertoire 'client'."; exit 1; }
python3 "$CLIENT_PATH" &
CLIENT_PID=$!

# Vérifier si le client est lancé
if ps -p "$CLIENT_PID" > /dev/null; then
    echo "Le client est lancé avec succès (PID: $CLIENT_PID)."
else
    echo "Échec du lancement du client." >&2
    exit 1
fi

# Résumé
echo "Les deux processus sont lancés avec succès."
echo "Server PID: $SERVER_PID"
echo "Client PID: $CLIENT_PID"
