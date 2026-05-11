"""
Page de test de connexion Business Central
Vérifie rapidement chaque endpoint avec $top=1
"""
import streamlit as st
import requests
from msal import ConfidentialClientApplication
from config.settings import BC_TENANT_ID, BC_CLIENT_ID, BC_CLIENT_SECRET, BC_SCOPE, ENDPOINTS

st.set_page_config(page_title="Test BC", page_icon="🔧")
st.title("🔧 Test de connexion Business Central")
st.markdown("Vérifie rapidement chaque endpoint sans charger toutes les données.")

def get_token():
    authority = f"https://login.microsoftonline.com/{BC_TENANT_ID}"
    app = ConfidentialClientApplication(BC_CLIENT_ID, authority=authority, client_credential=BC_CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=[BC_SCOPE])
    if "access_token" in result:
        return result["access_token"]
    raise RuntimeError(result.get("error_description", "Token error"))

def test_endpoint(key, url, token):
    # Add $top=1 to avoid loading all data
    test_url = url.split("?")[0] + "?$top=1"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
    }
    try:
        resp = requests.get(test_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            count = len(data.get("value", []))
            cols = list(data["value"][0].keys()) if count > 0 else []
            return "✅", f"{count} ligne(s)", cols[:5]
        else:
            return "❌", f"HTTP {resp.status_code}: {resp.reason}", []
    except Exception as e:
        return "❌", str(e)[:80], []

if st.button("🚀 Lancer le test de connexion", type="primary"):
    with st.spinner("Connexion à Azure AD..."):
        try:
            token = get_token()
            st.success("✅ Token Azure AD obtenu")
        except Exception as e:
            st.error(f"❌ Erreur token: {e}")
            st.stop()

    st.markdown("---")
    st.markdown("### 📋 Test des endpoints")

    results = []
    for key, url in ENDPOINTS.items():
        with st.spinner(f"Test {key}..."):
            status, msg, cols = test_endpoint(key, url, token)
            results.append({"Endpoint": key, "Statut": status, "Résultat": msg, "Colonnes (5 premiers)": ", ".join(cols)})

    import pandas as pd
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)

    ok = sum(1 for r in results if "✅" in r["Statut"])
    total = len(results)
    if ok == total:
        st.success(f"🎉 Tous les endpoints OK ({ok}/{total})")
    else:
        st.warning(f"⚠️ {ok}/{total} endpoints OK — vérifiez les erreurs ci-dessus")
