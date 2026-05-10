# GUIDE AZURE AD + BUSINESS CENTRAL (très détaillé)

Objectif : configurer l’authentification de l’application Streamlit vers Business Central via Azure AD (Microsoft Entra ID).

Contexte fourni :
- **Tenant ID** : `ad140881-5aae-4f5d-8941-89111ecfcdcc`
- **Tenant Name** : `Java distribution`
- **Application Azure AD existante** : OUI (mais ce guide couvre aussi la création)

---

## 1) Connexion au portail Azure

1. Ouvrez : https://portal.azure.com
2. Connectez-vous avec un compte administrateur (ou compte ayant droits App registrations).
3. Dans la barre de recherche en haut, tapez : **Microsoft Entra ID**.
4. Ouvrez le service.

### Capture d’écran textuelle (attendue)
- Barre de recherche Azure en haut
- Résultat « Microsoft Entra ID »
- Menu gauche : Overview, Users, App registrations

---

## 2) Choix : application existante ou nouvelle

### Option A — Utiliser l’application existante (recommandé ici)
1. Menu gauche Entra ID → **App registrations**.
2. Onglet **All applications**.
3. Recherchez votre application existante.
4. Cliquez dessus.

### Option B — Créer une nouvelle application
1. Entra ID → **App registrations** → **New registration**.
2. Renseignez :
   - **Name** : `JavaDistribution-Streamlit`
   - **Supported account types** : Single tenant
   - **Redirect URI** : laissez vide pour commencer (vous pourrez l’ajouter après)
3. Cliquez **Register**.

### Capture d’écran textuelle (attendue)
- Bouton **New registration**
- Formulaire Name / Supported account types / Redirect URI
- Bouton **Register**

---

## 3) Récupérer les identifiants nécessaires

Dans la page de l’application :

1. Dans **Overview**, copiez :
   - **Application (client) ID** → `BC_CLIENT_ID`
   - **Directory (tenant) ID** → `BC_TENANT_ID`
2. Vérifiez que Tenant ID = `ad140881-5aae-4f5d-8941-89111ecfcdcc`.

### Capture d’écran textuelle (attendue)
- Encadré avec : Application (client) ID
- Encadré avec : Directory (tenant) ID

---

## 4) Créer un Client Secret

1. Menu gauche de l’app → **Certificates & secrets**.
2. Onglet **Client secrets**.
3. Cliquez **New client secret**.
4. Description : `streamlit-cloud-secret`
5. Expiration : 6/12/24 mois selon politique interne.
6. Cliquez **Add**.
7. **IMPORTANT** : copiez immédiatement la colonne **Value** (visible une seule fois).
   - Cette valeur = `BC_CLIENT_SECRET`

### Capture d’écran textuelle (attendue)
- Bouton **New client secret**
- Tableau avec colonnes : Description / Expires / Value

---

## 5) Ajouter les permissions API Business Central

1. Menu gauche de l’app → **API permissions**.
2. Cliquez **Add a permission**.
3. Choisissez **APIs my organization uses**.
4. Recherchez : **Dynamics 365 Business Central**.
5. Sélectionnez les permissions nécessaires.

### Permissions recommandées
Pour les appels serveur-à-serveur (client credentials), ajoutez en priorité :
- **Application permissions** adaptées à vos endpoints OData
- Typiquement une permission type lecture/écriture Financials (selon votre tenant)

> Selon la configuration de votre tenant, le nom exact peut varier. Si vous ne voyez pas les permissions attendues, demandez à l’admin BC quelles permissions applicatives sont utilisées pour OData dans votre environnement.

6. Cliquez **Add permissions**.
7. Cliquez ensuite **Grant admin consent for <tenant>**.
8. Vérifiez que le statut devient **Granted for ...**.

### Capture d’écran textuelle (attendue)
- Bouton **Add a permission**
- API list incluant Dynamics 365 Business Central
- Bouton **Grant admin consent**
- Statut « Granted »

---

## 6) Configurer Redirect URI (pour compatibilité Streamlit)

Même si l’app actuelle utilise surtout client credentials, configurez aussi une Redirect URI propre.

1. Menu gauche → **Authentication**.
2. Cliquez **Add a platform**.
3. Choisissez **Web**.
4. Ajoutez :
   - `https://<votre-app>.streamlit.app`
   - (optionnel local) `http://localhost:8501`
5. Sauvegardez.

### Capture d’écran textuelle (attendue)
- Section Platform configurations
- Type Web
- Zone Redirect URIs
- Bouton Save

---

## 7) Vérification côté Business Central

Dans Business Central, vérifiez que l’application AAD est autorisée à lire les API/OData :

1. Ouvrez Business Central admin.
2. Vérifiez l’enregistrement application/service principal.
3. Vérifiez les rôles/permissions accordés aux tables/pages exposées via OData.

Si accès refusé (403/401), c’est souvent un problème de permissions BC et non de Streamlit.

---

## 8) Valeurs finales à reporter dans Streamlit Secrets

Vous aurez besoin de :

```toml
BC_TENANT_ID = "ad140881-5aae-4f5d-8941-89111ecfcdcc"
BC_CLIENT_ID = "<application-client-id>"
BC_CLIENT_SECRET = "<client-secret-value>"
BC_SCOPE = "https://api.businesscentral.dynamics.com/.default"
BC_ENVIRONMENT = "Production"
BC_COMPANY = "JAVA Distribution"
```

---

## 9) Erreurs courantes

### AADSTS7000215 / invalid client secret
- Le secret copié est mauvais ou expiré.
- Recréez un secret et remplacez dans Streamlit Secrets.

### AADSTS700016 / application not found
- Mauvais Client ID ou mauvais tenant.
- Vérifiez BC_CLIENT_ID + BC_TENANT_ID.

### 401 Unauthorized sur OData
- Token OK mais permission BC insuffisante.
- Vérifiez API permissions + admin consent + droits BC.

### 404 endpoint OData
- Mauvais nom d’environnement (`Production`) ou nom de société (`JAVA Distribution`).
- Vérifiez aussi la publication des web services BC.

---

Ensuite, suivez `docs/GUIDE_STREAMLIT_CLOUD.md` pour le déploiement final.
