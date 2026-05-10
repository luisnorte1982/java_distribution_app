# 🚀 Guide de Déploiement — Java Distribution Reporting

## Partie 1 : Connexion Business Central (OAuth2)

### Étape 1 — Créer l'App Registration Azure AD

1. Allez sur **[Azure Portal](https://portal.azure.com)** → Azure Active Directory → App registrations
2. Cliquez **"New registration"**
3. Remplissez :
   - **Name** : `Java Distribution Reporting`
   - **Supported account types** : "Accounts in this organizational directory only"
   - **Redirect URI** : laisser vide (pas nécessaire pour client_credentials)
4. Cliquez **Register**

### Étape 2 — Récupérer les identifiants

Après la création, notez :
- **Application (client) ID** → c'est votre `BC_CLIENT_ID`
- **Directory (tenant) ID** → déjà configuré : `ad140881-5aae-4f5d-8941-89111ecfcdcc`

### Étape 3 — Créer un Client Secret

1. Dans l'app registration → **Certificates & secrets**
2. Cliquez **"New client secret"**
3. Description : `Streamlit Reporting`
4. Expiration : 24 months (recommandé)
5. Cliquez **Add**
6. **COPIEZ IMMÉDIATEMENT** la valeur → c'est votre `BC_CLIENT_SECRET`

### Étape 4 — Configurer les permissions API

1. Dans l'app registration → **API permissions**
2. Cliquez **"Add a permission"**
3. Choisissez **"Dynamics 365 Business Central"**
4. Sélectionnez **"Application permissions"**
5. Cochez :
   - `API.ReadWrite.All`
   - `Automation.ReadWrite.All` (optionnel)
6. Cliquez **"Add permissions"**
7. **IMPORTANT** : Cliquez **"Grant admin consent for [votre tenant]"**

### Étape 5 — Autoriser l'app dans Business Central

1. Ouvrez **Business Central** → Administration → Azure AD Applications
2. Cliquez **"New"**
3. Remplissez :
   - **Client ID** : collez votre Application (client) ID
   - **Description** : `Streamlit Reporting App`
   - **State** : `Enabled`
4. Dans la section **User Permission Sets**, ajoutez :
   - `D365 FULL ACCESS` ou au minimum :
   - `D365 READ` (pour lecture seule des données)

### Étape 6 — Configurer l'application

Créez le fichier `.env` dans le dossier de l'application :

```env
BC_TENANT_ID=ad140881-5aae-4f5d-8941-89111ecfcdcc
BC_CLIENT_ID=votre-client-id-ici
BC_CLIENT_SECRET=votre-client-secret-ici
BC_SCOPE=https://api.businesscentral.dynamics.com/.default
```

---

## Partie 2 : Mise en ligne

### Option A : Streamlit Community Cloud (GRATUIT — Recommandé pour commencer)

**Prérequis** : un repo GitHub

1. **Pousser le code sur GitHub** :
   ```bash
   # Créer un repo sur github.com (privé recommandé)
   git remote add origin https://github.com/VOTRE-USER/java-distribution-reporting.git
   git branch -M main
   git push -u origin main
   ```

2. **Déployer sur Streamlit Cloud** :
   - Allez sur [share.streamlit.io](https://share.streamlit.io)
   - Connectez votre compte GitHub
   - Cliquez "New app"
   - Sélectionnez votre repo, branche `main`, fichier `app.py`
   - Dans **Advanced settings** → **Secrets**, ajoutez :
     ```toml
     BC_TENANT_ID = "ad140881-5aae-4f5d-8941-89111ecfcdcc"
     BC_CLIENT_ID = "votre-client-id"
     BC_CLIENT_SECRET = "votre-client-secret"
     BC_SCOPE = "https://api.businesscentral.dynamics.com/.default"
     ```
   - Cliquez **Deploy!**

**Avantages** : gratuit, HTTPS automatique, mise à jour auto depuis GitHub
**Limitations** : 1 Go RAM, peut s'endormir après inactivité

### Option B : Azure App Service (Recommandé pour production)

Idéal car votre tenant Azure est déjà configuré.

1. **Créer un Dockerfile** :
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8501
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Déployer** :
   ```bash
   # Azure CLI
   az webapp up --name java-distribution-reporting --runtime PYTHON:3.11
   ```

3. **Configurer les variables d'environnement** dans le portail Azure → App Service → Configuration

### Option C : VPS / Serveur dédié

Si vous avez un serveur Linux :

```bash
# Sur votre serveur
git clone https://github.com/VOTRE-USER/java-distribution-reporting.git
cd java-distribution-reporting
pip install -r requirements.txt
cp .env.example .env
# Éditez .env avec vos credentials

# Lancer en production avec systemd
sudo nano /etc/systemd/system/java-reporting.service
```

Contenu du service systemd :
```ini
[Unit]
Description=Java Distribution Reporting
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/java-distribution-reporting
ExecStart=/usr/bin/streamlit run app.py --server.port 8501 --server.headless true
Restart=always
EnvironmentFile=/opt/java-distribution-reporting/.env

[Install]
WantedBy=multi-user.target
```

Puis :
```bash
sudo systemctl enable java-reporting
sudo systemctl start java-reporting
```

Ajoutez un **reverse proxy Nginx** avec SSL :
```nginx
server {
    listen 443 ssl;
    server_name reporting.javadistribution.lu;
    
    ssl_certificate /etc/letsencrypt/live/reporting.javadistribution.lu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/reporting.javadistribution.lu/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## Partie 3 : Sécurité & Bonnes pratiques

### Checklist avant mise en production
- [ ] `.env` n'est PAS dans le repo git (vérifié via `.gitignore`)
- [ ] Le Client Secret a une date d'expiration raisonnable (12-24 mois)
- [ ] L'app Azure AD a uniquement les permissions nécessaires (lecture)
- [ ] Streamlit est en mode `headless=true` en production
- [ ] HTTPS est activé (certificat SSL)
- [ ] Le fichier `VE_Fige_2025.xlsx` est uploadé ou accessible

### Renouvellement du Client Secret
Le secret Azure AD expire. Mettez un rappel pour le renouveler :
1. Azure Portal → App Registration → Certificates & secrets
2. Créer un nouveau secret
3. Mettre à jour `.env` ou les secrets Streamlit Cloud
4. Redémarrer l'application

---

*Guide créé le 9 mai 2026 — Java Distribution*
