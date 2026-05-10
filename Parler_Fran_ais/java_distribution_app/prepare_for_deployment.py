"""
Script de préparation au déploiement Streamlit Cloud.
- Vérifie les fichiers requis
- Liste les secrets à configurer
- Génère deployment_checklist.md
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CHECKLIST_PATH = PROJECT_ROOT / "deployment_checklist.md"

REQUIRED_FILES = [
    "app.py",
    "requirements.txt",
    "README.md",
    "config/settings.py",
    ".streamlit/config.toml",
    ".streamlit/secrets.toml.example",
    ".gitignore",
    "docs/GUIDE_GITHUB.md",
    "docs/GUIDE_AZURE_AD.md",
    "docs/GUIDE_STREAMLIT_CLOUD.md",
]

RECOMMENDED_FILES = [
    ".env.example",
    "run.sh",
    "prepare_for_deployment.py",
]

REQUIRED_SECRETS = [
    "BC_TENANT_ID",
    "BC_CLIENT_ID",
    "BC_CLIENT_SECRET",
    "BC_SCOPE",
    "BC_ENVIRONMENT",
    "BC_COMPANY",
]


def check_files(file_list: list[str]) -> list[tuple[str, bool]]:
    results: list[tuple[str, bool]] = []
    for relative_path in file_list:
        exists = (PROJECT_ROOT / relative_path).exists()
        results.append((relative_path, exists))
    return results


def detect_local_secret(secret_name: str) -> bool:
    """Vérifie uniquement si une variable est présente localement dans l'environnement."""
    return bool(os.getenv(secret_name))


def markdown_status(ok: bool) -> str:
    return "✅" if ok else "❌"


def build_checklist_markdown(
    required_files_status: list[tuple[str, bool]],
    recommended_files_status: list[tuple[str, bool]],
    secret_status: list[tuple[str, bool]],
) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    required_ok = all(status for _, status in required_files_status)
    recommended_ok = all(status for _, status in recommended_files_status)

    lines = [
        "# Checklist de déploiement Streamlit Cloud",
        "",
        f"Généré le : **{generated_at}**",
        "",
        "## 1) Fichiers obligatoires",
        "",
    ]

    for file_path, status in required_files_status:
        lines.append(f"- [{ 'x' if status else ' ' }] {file_path} {markdown_status(status)}")

    lines.extend([
        "",
        f"**Statut global fichiers obligatoires : {markdown_status(required_ok)}**",
        "",
        "## 2) Fichiers recommandés",
        "",
    ])

    for file_path, status in recommended_files_status:
        lines.append(f"- [{ 'x' if status else ' ' }] {file_path} {markdown_status(status)}")

    lines.extend([
        "",
        f"**Statut global fichiers recommandés : {markdown_status(recommended_ok)}**",
        "",
        "## 3) Secrets à configurer dans Streamlit Cloud",
        "",
        "> Vérification locale indicative (les secrets réels doivent être saisis dans Streamlit Cloud > Settings > Secrets).",
        "",
    ])

    for secret_name, status in secret_status:
        lines.append(f"- [ ] {secret_name} (présent localement: {markdown_status(status)})")

    lines.extend([
        "",
        "### Bloc TOML à copier dans Streamlit Cloud",
        "",
        "```toml",
        'BC_TENANT_ID = "ad140881-5aae-4f5d-8941-89111ecfcdcc"',
        'BC_CLIENT_ID = "<votre-client-id>"',
        'BC_CLIENT_SECRET = "<votre-client-secret>"',
        'BC_SCOPE = "https://api.businesscentral.dynamics.com/.default"',
        'BC_ENVIRONMENT = "Production"',
        'BC_COMPANY = "JAVA Distribution"',
        "```",
        "",
        "## 4) Étapes finales avant mise en production",
        "",
        "- [ ] Repository GitHub privé (recommandé)",
        "- [ ] Dernier commit poussé sur la branche de déploiement",
        "- [ ] Secrets configurés dans Streamlit Cloud",
        "- [ ] Test connexion Business Central réussi",
        "- [ ] Vérification des pages principales (KPI + filtres + exports)",
        "- [ ] Aucun secret en clair dans le code ou dans le repo",
        "",
        "## 5) Références documentation",
        "",
        "- docs/GUIDE_GITHUB.md",
        "- docs/GUIDE_AZURE_AD.md",
        "- docs/GUIDE_STREAMLIT_CLOUD.md",
        "",
    ])

    return "\n".join(lines)


def main() -> None:
    print("🔎 Vérification de la préparation au déploiement…")

    required_files_status = check_files(REQUIRED_FILES)
    recommended_files_status = check_files(RECOMMENDED_FILES)
    secret_status = [(secret, detect_local_secret(secret)) for secret in REQUIRED_SECRETS]

    checklist_content = build_checklist_markdown(
        required_files_status=required_files_status,
        recommended_files_status=recommended_files_status,
        secret_status=secret_status,
    )
    CHECKLIST_PATH.write_text(checklist_content, encoding="utf-8")

    missing_required = [fp for fp, ok in required_files_status if not ok]

    print(f"📝 Checklist générée: {CHECKLIST_PATH}")
    if missing_required:
        print("⚠️ Fichiers obligatoires manquants:")
        for fp in missing_required:
            print(f"   - {fp}")
    else:
        print("✅ Tous les fichiers obligatoires sont présents.")

    print("🔐 Secrets à renseigner dans Streamlit Cloud:")
    for secret, present in secret_status:
        print(f"   - {secret}: {'présent localement' if present else 'non détecté localement'}")


if __name__ == "__main__":
    main()
