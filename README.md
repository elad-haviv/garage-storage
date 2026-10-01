# garage-storage

S3-compatible file storage for internal apps, deployed on Coolify.

**What's running:** [Garage](https://garagehq.deuxfleurs.fr) v2.3.0 — a lightweight,
open-source (AGPLv3) S3-compatible object store. Single node, replication mode `1`,
LMDB metadata, named Docker volumes (`garage_meta`, `garage_data`) so data survives
redeploys.

**Endpoints**
| URL | Purpose |
|---|---|
| `https://s3.haviv.pro` | S3 API (path-style: `https://s3.haviv.pro/<bucket>/<key>`) |
| `https://garage-admin.haviv.pro` | Admin API + built-in web UI |

Region: `garage`. Auth is standard AWS SigV4 with per-app access keys.

**Admin**
```bash
# layout (run once after first deploy, via admin API):
curl -H "Authorization: Bearer $GARAGE_ADMIN_TOKEN" \
  -X POST https://garage-admin.haviv.pro/v2/UpdateClusterLayout \
  -d '{"parameters":{"zone_redundancy":"off"}}'
# then GET /v2/GetClusterLayout, set capacity on the node, POST ApplyClusterLayout
```

**Per-app access** — each app gets its own bucket + S3 key:
```bash
curl -H "Authorization: Bearer $GARAGE_ADMIN_TOKEN" \
  -X POST https://garage-admin.haviv.pro/v2/CreateBucket -d '{"globalAlias":"myapp"}'
curl -H "Authorization: Bearer $GARAGE_ADMIN_TOKEN" \
  -X POST https://garage-admin.haviv.pro/v2/CreateKey -d '{"name":"myapp"}'
```

**Client example (boto3):**
```python
import boto3
s3 = boto3.client(
    "s3",
    endpoint_url="https://s3.haviv.pro",
    region_name="garage",
    aws_access_key_id="<KEY_ID>",
    aws_secret_access_key="<SECRET>",
)
s3.put_object(Bucket="myapp", Key="hello.txt", Body=b"hi")
```

Deploys: push to `main` → Coolify (docker-compose build pack). Secrets live in
Coolify env vars (`GARAGE_ADMIN_TOKEN`, `GARAGE_RPC_SECRET`) — never in this repo.
