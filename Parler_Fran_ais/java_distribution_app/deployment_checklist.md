# Checklist de déploiement Streamlit Cloud

Généré le : **2026-05-10 07:20:40**

## 1) Fichiers obligatoires

- [x] app.py ✅
- [x] requirements.txt ✅
- [x] README.md ✅
- [x] config/settings.py ✅
- [x] .streamlit/config.toml ✅
- [x] .streamlit/secrets.toml.example ✅
- [x] .gitignore ✅
- [x] docs/GUIDE_GITHUB.md ✅
- [x] docs/GUIDE_AZURE_AD.md ✅
- [x] docs/GUIDE_STREAMLIT_CLOUD.md ✅

**Statut global fichiers obligatoires : ✅**

## 2) Fichiers recommandés

- [x] .env.example ✅
- [x] run.sh ✅
- [x] prepare_for_deployment.py ✅

**Statut global fichiers recommandés : ✅**

## 3) Secrets à configurer dans Streamlit Cloud

> Vérification locale indicative (les secrets réels doivent être saisis dans Streamlit Cloud > Settings > Secrets).

- [ ] BC_TENANT_ID (présent localement: ❌)
- [ ] BC_CLIENT_ID (présent localement: ❌)
- [ ] BC_CLIENT_SECRET (présent localement: ❌)
- [ ] BC_SCOPE (présent localement: ❌)
- [ ] BC_ENVIRONMENT (présent localement: ❌)
- [ ] BC_COMPANY (présent localement: ❌)

### Bloc TOML à copier dans Streamlit Cloud

```toml
BC_TENANT_ID = "ad140881-5aae-4f5d-8941-89111ecfcdcc"
BC_CLIENT_ID = "<votre-client-id>"
BC_CLIENT_SECRET = "<votre-client-secret>"
BC_SCOPE = "https://api.businesscentral.dynamics.com/.default"
BC_ENVIRONMENT = "Production"
BC_COMPANY = "JAVA Distribution"
```

## 4) Étapes finales avant mise en production

- [ ] Repository GitHub privé (recommandé)
- [ ] Dernier commit poussé sur la branche de déploiement
- [ ] Secrets configurés dans Streamlit Cloud
- [ ] Test connexion Business Central réussi
- [ ] Vérification des pages principales (KPI + filtres + exports)
- [ ] Aucun secret en clair dans le code ou dans le repo

## 5) Références documentation

- docs/GUIDE_GITHUB.md
- docs/GUIDE_AZURE_AD.md
- docs/GUIDE_STREAMLIT_CLOUD.md
