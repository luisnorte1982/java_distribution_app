# ☕ Java Distribution — Reporting Dashboard

Application **Streamlit** pour le reporting des revenus/marges Java Distribution, avec 2 modes :
- **Business Central (live)** via OData + Azure AD
- **Excel (démo)** via fichier uploadé ou local

---

## 🧱 Architecture de l'application

```text
java_distribution_app/
├── app.py                          # Entrée principale Streamlit
├── config/
│   └── settings.py                 # Config BC/Azure/constantes
├── utils/
│   ├── odata_client.py             # OAuth2 + appels OData
│   ├── data_processor.py           # Préparation tables & enrichissement
│   ├── measures.py                 # Mesures type DAX (Python/Pandas)
│   └── ui_helpers.py               # Helpers UI
├── pages/                          # Pages dashboard (multi-pages)
├── .streamlit/
│   ├── config.toml                 # Config UI Streamlit Cloud
│   └── secrets.toml.example        # Modèle de secrets
├── docs/
│   ├── GUIDE_GITHUB.md             # Guide GitHub (débutant)
│   ├── GUIDE_AZURE_AD.md           # Guide Azure AD + BC
│   └── GUIDE_STREAMLIT_CLOUD.md    # Guide déploiement Streamlit Cloud
├── prepare_for_deployment.py       # Vérification readiness déploiement
├── requirements.txt
└── .gitignore
```

---

## 🚀 Déploiement Streamlit Cloud (résumé rapide)

1. Publier ce code sur GitHub
2. Créer l’app sur Streamlit Cloud (main file: `app.py`)
3. Configurer les secrets dans Streamlit
4. Démarrer l’app en mode **Business Central (live)**

Secrets attendus :

```toml
BC_TENANT_ID = "ad140881-5aae-4f5d-8941-89111ecfcdcc"
BC_CLIENT_ID = "<client-id>"
BC_CLIENT_SECRET = "<client-secret>"
BC_SCOPE = "https://api.businesscentral.dynamics.com/.default"
BC_ENVIRONMENT = "Production"
BC_COMPANY = "JAVA Distribution"
```

---

## 📚 Guides détaillés (en français)

- **Guide GitHub débutant** : [`docs/GUIDE_GITHUB.md`](docs/GUIDE_GITHUB.md)
- **Guide Azure AD / Business Central** : [`docs/GUIDE_AZURE_AD.md`](docs/GUIDE_AZURE_AD.md)
- **Guide Streamlit Cloud** : [`docs/GUIDE_STREAMLIT_CLOUD.md`](docs/GUIDE_STREAMLIT_CLOUD.md)

Ces guides sont volontairement détaillés pour une personne qui débute.

---

## ⚙️ Lancement local (optionnel)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Mode cloud recommandé : Business Central live.

---

## ✅ Préparation avant déploiement

Exécuter :

```bash
python prepare_for_deployment.py
```

Le script :
- vérifie les fichiers critiques
- vérifie les variables/secrets nécessaires
- génère `deployment_checklist.md`

---

## 🔒 Sécurité

- Ne jamais commiter `.env` ou `.streamlit/secrets.toml`
- Régénérer le client secret en cas d’exposition
- Préférer un repository GitHub **privé**

---

*Version déploiement cloud — Mai 2026*
