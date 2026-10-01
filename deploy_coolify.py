#!/usr/bin/env python3
"""Register garage-storage in Coolify as a docker-compose SERVICE.
This Coolify version exposes compose creation via POST /services (not
/applications/dockercompose). Flow: create (no deploy) -> set env vars
-> verify literal -> deploy. Secrets never printed."""
import base64, json, os, secrets, sys, urllib.request

def api(method, path, payload=None):
    url = BASE + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
        headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode()
            return r.status, (json.loads(body) if body.strip() else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]

ENV_PATH = "/opt/data/.env"
env = dict(os.environ)  # COOLIFY_* are injected into terminal sessions by the sandbox
for line in open(ENV_PATH):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        env.setdefault(k, v)

BASE = env["COOLIFY_API_URL"].replace("http://http://", "http://")
TOKEN = env["COOLIFY_API_TOKEN"]
PROJECT = "asukajc3hlxyqbmzovvkyur7"       # Data Store
SERVER = "qng68v9vqad1bqab5vqca7rr"

# 1. ensure secrets exist in .env (generate if missing; never print)
changed = False
for k in ("GARAGE_ADMIN_TOKEN", "GARAGE_RPC_SECRET"):
    if not env.get(k):
        env[k] = secrets.token_hex(32)
        changed = True
if changed:
    with open(ENV_PATH, "a") as f:
        for k in ("GARAGE_ADMIN_TOKEN", "GARAGE_RPC_SECRET"):
            if not any(l.startswith(k + "=") for l in open(ENV_PATH)):
                f.write(f"\n{k}={env[k]}")
    print("secrets: generated + appended to .env (not shown)")
else:
    print("secrets: already present in .env")

# 2. create the compose SERVICE (instant_deploy=false so envs land first)
raw = base64.b64encode(open("/opt/data/projects/garage-storage/docker-compose.yml", "rb").read()).decode()
status, resp = api("POST", "/services", {
    "name": "garage-storage",
    "description": "S3-compatible file storage (Garage) for internal apps",
    "project_uuid": PROJECT,
    "server_uuid": SERVER,
    "environment_name": "production",
    "docker_compose_raw": raw,
    "instant_deploy": False,
})
print("create:", status, json.dumps(resp)[:400] if isinstance(resp, dict) else str(resp)[:400])
if status not in (200, 201) or not (isinstance(resp, dict) and resp.get("uuid")):
    sys.exit("create failed")
APP = resp["uuid"]
print("service uuid:", APP)

# 3. set env vars on the SERVICE (is_literal so they reach the container)
for k in ("GARAGE_ADMIN_TOKEN", "GARAGE_RPC_SECRET"):
    s, r = api("POST", f"/services/{APP}/envs", {"key": k, "value": env[k], "is_literal": True})
    print(f"env {k}: {s} {str(r)[:120]}")

# 4. verify they stored as literals (values hidden by design)
s, r = api("GET", f"/services/{APP}/envs")
if isinstance(r, list):
    print("envs verify:", [(e.get("key"), e.get("is_literal")) for e in r])
else:
    print("envs verify: unexpected:", str(r)[:200])

# 5. deploy
s, r = api("POST", f"/deploy?uuid={APP}&force=true")
print("deploy:", s, str(r)[:200])

with open("/opt/data/projects/garage-storage/.coolify_service_uuid", "w") as f:
    f.write(APP)
print("OK — poll GET /services/" + APP)
