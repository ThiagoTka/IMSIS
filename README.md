gcloud run deploy imsis --source .

git add .
git commit -m "Secrets v2"
git push


--------------Cores---------------

:root {
  --bg-main: #F9FAFB;
  --bg-card: #FFFFFF;
  --bg-sidebar: #0F2A44;

  --text-main: #1F2933;
  --text-secondary: #4B5563;

  --primary: #1F4E79;
  --success: #16A34A;
  --warning: #F59E0B;
  --danger: #DC2626;
}

[data-theme="dark"] {
  --bg-main: #0B1220;
  --bg-card: #111827;
  --bg-sidebar: #020617;

  --text-main: #E5E7EB;
  --text-secondary: #9CA3AF;

  --primary: #3B82F6;
  --success: #22C55E;
  --warning: #FBBF24;
  --danger: #EF4444;
}