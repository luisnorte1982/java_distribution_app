# GUIDE STREAMLIT CLOUD (déploiement complet)

Objectif : publier l’application Streamlit depuis GitHub vers Streamlit Community Cloud.

---

## 1) Prérequis

Avant de commencer, vous devez avoir :
- un compte GitHub (voir `GUIDE_GITHUB.md`)
- le code du projet dans un repository GitHub
- les identifiants Azure AD/Business Central (voir `GUIDE_AZURE_AD.md`)

---

## 2) Créer un compte Streamlit Cloud

1. Ouvrez : https://share.streamlit.io
2. Cliquez **Sign in with GitHub**.
3. Autorisez Streamlit à accéder à vos repositories GitHub.
4. Une fois connecté, vous arrivez sur le dashboard Streamlit Cloud.

### Capture d’écran textuelle (attendue)
- Bouton **Sign in with GitHub**
- Écran GitHub d’autorisation OAuth
- Tableau de bord Streamlit avec bouton **New app**

---

## 3) Créer une nouvelle application

1. Cliquez **New app**.
2. Sélectionnez :
   - **Repository** : votre repo (ex: `votre_user/java_distribution_app`)
   - **Branch** : `main` (ou `master` selon votre repo)
   - **Main file path** : `app.py`
3. Cliquez **Deploy**.

> Streamlit installe automatiquement les dépendances depuis `requirements.txt`.

### Capture d’écran textuelle (attendue)
- Formulaire New app
- Champs Repository / Branch / Main file path
- Bouton **Deploy**

---

## 4) Configurer les secrets (obligatoire)

Une fois l’app créée :

1. Ouvrez l’app dans Streamlit Cloud.
2. Cliquez sur **⋮** (menu) puis **Settings**.
3. Ouvrez l’onglet **Secrets**.
4. Collez la configuration ci-dessous (en remplaçant les valeurs) :

```toml
BC_TENANT_ID = "ad140881-5aae-4f5d-8941-89111ecfcdcc"
BC_CLIENT_ID = "<votre-client-id>"
BC_CLIENT_SECRET = "<votre-client-secret>"
BC_SCOPE = "https://api.businesscentral.dynamics.com/.default"
BC_ENVIRONMENT = "Production"
BC_COMPANY = "JAVA Distribution"
```

5. Cliquez **Save**.
6. Redémarrez l’app si nécessaire (Reboot).

### Capture d’écran textuelle (attendue)
- Onglet **Secrets**
- Zone texte TOML
- Bouton **Save**

---

## 5) Premier lancement et vérification

Dans l’application :
1. Sélectionnez **🔗 Business Central (live)**.
2. Cliquez **🔄 Charger depuis Business Central**.
3. Vérifiez :
   - Pas d’erreur d’authentification
   - Les KPI s’affichent
   - Les pages latérales contiennent des données

---

## 6) Mode démo sans fichier local (cloud)

En Streamlit Cloud, les fichiers locaux Excel ne sont pas garantis.

Comportement prévu dans cette application :
- Si aucun `CONSOLIDE1.xlsx` local n’existe, le mode live est privilégié.
- Vous pouvez uploader un `CONSOLIDE1.xlsx` via la sidebar pour une session de démonstration.

---

## 7) Mise à jour de l’application

À chaque modification du code sur GitHub :
1. Streamlit peut redéployer automatiquement.
2. Sinon, ouvrez l’app → **Reboot app**.

---

## 8) Troubleshooting courant

### Erreur: Module not found
- Vérifiez `requirements.txt`.
- Faites **Reboot app**.

### Erreur: Token acquisition failed
- Vérifiez `BC_TENANT_ID`, `BC_CLIENT_ID`, `BC_CLIENT_SECRET`.
- Vérifiez expiration du secret Azure AD.

### Erreur: 401 / 403 sur OData
- Permissions API ou droits Business Central insuffisants.
- Vérifiez Admin consent dans Azure AD + droits BC.

### Erreur: 404 Company not found
- Vérifiez exactitude de `BC_COMPANY` (`JAVA Distribution`).
- Vérifiez l’environnement `Production`.

### L’app démarre mais aucune donnée
- Vérifiez que les endpoints OData utilisés existent dans votre BC.
- Testez en mode live puis avec un fichier Excel uploadé pour isoler le problème.

---

## 9) Check final avant passage en production

- [ ] Repo GitHub privé
- [ ] Secrets configurés dans Streamlit (et jamais dans le code)
- [ ] Client Secret non expiré
- [ ] Permissions Dynamics 365 Business Central validées
- [ ] Chargement live OK sur plusieurs pages
- [ ] Documentation interne mise à jour

---

Déploiement terminé ✅
