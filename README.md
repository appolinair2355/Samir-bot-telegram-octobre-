# Bot Telegram - Système de Prédictions Excel

## Déploiement sur Render.com

### Configuration requise

1. **Variables d'environnement** :
   - `BOT_TOKEN` : Token de votre bot Telegram
   - `WEBHOOK_URL` : URL de votre application (ex: https://votre-app.onrender.com)
   - `ADMIN_ID` : Votre ID Telegram (1190237801)
   - `PORT` : 10000 (déjà configuré)

2. **Fichier Excel** :
   - Le fichier `predictions.xlsx` doit contenir 2 colonnes : `Numero` et `Costume`
   - Formats acceptés pour Costume : Pique, Cœur, Carreau, Trèfle (ou emojis ♠️♥️♦️♣️)

### Instructions de déploiement

1. Créez un nouveau Web Service sur Render.com
2. Uploadez ce fichier ZIP
3. Configurez les variables d'environnement
4. Le bot démarrera automatiquement sur le port 10000

### Commandes disponibles

- `/excel_stats` - Statistiques des prédictions
- `/excel_reload` - Recharger le fichier Excel
- `/excel_list` - Liste des prédictions à venir

### Support

Pour toute question, contactez l'administrateur du bot.
