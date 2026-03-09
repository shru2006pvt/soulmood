# SoulMood Deployment

This app is ready for permanent deployment.

## Option A (Recommended): Render + GitHub (stable URL)

1. Create a new empty GitHub repository named `soulmood`.
2. Push this project:

```bash
git init
git add .
git commit -m "Initial deploy"
git branch -M main
git remote add origin https://github.com/<your-username>/soulmood.git
git push -u origin main
```

3. Open Render dashboard: `https://dashboard.render.com/`.
4. Click **New +** -> **Blueprint**.
5. Connect your GitHub repo and select `soulmood`.
6. Render auto-detects `render.yaml` and deploys.
7. Your app URL will be: `https://<service-name>.onrender.com`.

## Option B: Streamlit Community Cloud

1. Push this repo to GitHub.
2. Open `https://share.streamlit.io/`.
3. Deploy app:
- Repository: `<your-username>/soulmood`
- Branch: `main`
- Main file path: `app.py`

Notes:
- Current app stores data in local files (`data/*.csv`, `data/*.json`). On cloud hosts this may reset between restarts.
- For persistent user data, use a database (Supabase, Firebase, Postgres, etc.).
