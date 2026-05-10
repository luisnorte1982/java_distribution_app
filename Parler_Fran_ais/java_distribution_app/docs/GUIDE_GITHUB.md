# GUIDE GITHUB (débutant complet)

Ce guide explique **pas à pas** comment créer votre compte GitHub et publier le projet **sans ligne de commande Git** (uniquement via le site web).

---

## 1) Créer un compte GitHub

1. Ouvrez votre navigateur et allez sur : https://github.com/
2. Cliquez sur **Sign up** (en haut à droite).
3. Renseignez :
   - **Email**
   - **Password**
   - **Username** (nom public de votre compte)
4. Cliquez sur **Continue**.
5. Vérifiez votre email avec le code reçu.
6. Connectez-vous ensuite sur GitHub.

### Capture d’écran textuelle (attendue)
- En haut à droite : bouton **Sign up**
- Formulaire central avec Email / Password / Username
- Bouton **Create account** ou **Continue**

---

## 2) Créer un nouveau repository

1. Une fois connecté, cliquez sur votre photo de profil (en haut à droite).
2. Cliquez sur **Your repositories**.
3. Cliquez sur le bouton vert **New**.
4. Remplissez :
   - **Repository name** : `java_distribution_app`
   - **Description** (optionnel) : `Dashboard Streamlit Java Distribution`
   - **Visibility** :
     - `Private` recommandé (données entreprise)
     - `Public` seulement si vous voulez partager publiquement
5. Cochez **Add a README file** uniquement si vous partez de zéro.
   - Dans votre cas, le projet contient déjà un README, donc laissez décoché si possible.
6. Cliquez sur **Create repository**.

### Capture d’écran textuelle (attendue)
- Titre de page : **Create a new repository**
- Champ **Repository name**
- Options **Public / Private**
- Bouton vert **Create repository**

---

## 3) Uploader le code via interface web (sans terminal)

> Méthode recommandée débutant : **Upload files** depuis la page du repository.

1. Ouvrez votre repository vide (ex: `https://github.com/<votre_user>/java_distribution_app`).
2. Cliquez sur **Add file** puis **Upload files**.
3. Ouvrez l’explorateur de fichiers de votre ordinateur.
4. Glissez-déposez le contenu du dossier projet (fichiers + sous-dossiers) dans GitHub.
5. Patientez jusqu’à la fin de l’upload.
6. En bas de page, dans **Commit changes** :
   - Message : `Initial upload streamlit app`
   - Cliquez **Commit changes**.

### Important (fichiers à NE PAS envoyer)
Assurez-vous de **ne pas uploader** les secrets :
- `.env`
- `.streamlit/secrets.toml`
- Fichiers Excel sensibles internes non nécessaires

Le fichier `.gitignore` du projet aide à éviter cela, mais vérifiez visuellement avant commit.

### Capture d’écran textuelle (attendue)
- Zone drag-and-drop « Upload files »
- Liste des fichiers en attente
- Bloc **Commit changes** en bas
- Bouton vert **Commit changes**

---

## 4) Vérifier que tout est bien publié

Après le commit, vous devez voir au minimum :
- `app.py`
- `requirements.txt`
- `config/settings.py`
- dossier `pages/`
- dossier `.streamlit/`
- dossier `docs/`

Si un fichier manque :
1. Cliquez **Add file** > **Upload files**
2. Ajoutez le fichier manquant
3. Commit

---

## 5) Mettre à jour le code plus tard (toujours sans terminal)

### Modifier un fichier existant
1. Ouvrez le fichier sur GitHub.
2. Cliquez sur l’icône **crayon** (Edit this file).
3. Modifiez le texte.
4. Descendez en bas.
5. **Commit changes**.

### Ajouter un nouveau fichier
1. **Add file** > **Create new file**
2. Nom + contenu
3. **Commit changes**

### Supprimer un fichier
1. Ouvrez le fichier
2. Cliquez sur **...** puis **Delete file**
3. **Commit changes**

---

## 6) Bonnes pratiques simples

- Utilisez des messages de commit clairs :
  - `Ajout guide Streamlit Cloud`
  - `Correction config Business Central`
- Préférez repository **Private** pour un projet métier.
- N’ajoutez jamais de client secret dans un fichier versionné.

---

## 7) Problèmes fréquents et solutions

### Problème: "File too large"
- GitHub web refuse certains fichiers volumineux.
- Solution : n’uploadez pas les gros fichiers Excel, ou compressez/filtrez.

### Problème: j’ai publié un secret par erreur
1. Supprimez le secret du fichier immédiatement
2. Commit
3. **Régénérez le secret Azure AD** (important)

### Problème: je ne trouve pas mon repository
- Vérifiez en haut à droite votre compte connecté.
- Allez dans **Your repositories**.

---

Vous pouvez maintenant passer au guide Streamlit Cloud (`docs/GUIDE_STREAMLIT_CLOUD.md`).
