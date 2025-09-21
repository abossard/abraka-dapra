# Secrets Directory

Holds local secret material for the file-based Dapr secret store component.

Files:
- `secrets.json` (gitignored) – actual runtime secrets
- `secrets.json.sample` – template checked into version control

Update `components/secretstore.yaml` if you relocate this directory.
