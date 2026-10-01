# garage-storage

S3-compatible file storage for internal apps — [Garage](https://garagehq.deuxfleurs.fr) v2.3.0
on Coolify, deployed as a single Dockerfile application from this repo.

| URL | Purpose |
|---|---|
| `https://s3.haviv.pro` | S3 API (path-style: `https://s3.haviv.pro/<bucket>/<key>`) |
| `https://garage-admin.haviv.pro` | Admin API (v2 endpoints, bearer token) |

Region: `garage`. Auth: standard AWS SigV4 per-app keys.
Secrets live in Coolify env vars (`GARAGE_ADMIN_TOKEN`, `GARAGE_RPC_SECRET`) — never in git.
`garage.toml` is baked into the image at build time.

## Admin (v2 API, all paths need `Authorization: Bearer $GARAGE_ADMIN_TOKEN`)

```bash
H="Authorization: Bearer $GARAGE_ADMIN_TOKEN"
U=https://garage-admin.haviv.pro

# cluster status / layout
curl -H "$H" $U/v2/GetClusterStatus
curl -H "$H" $U/v2/GetClusterLayout

# new bucket
curl -H "$H" -X POST $U/v2/CreateBucket -d '{"globalAlias":"myapp"}'
# new key for an app
curl -H "$H" -X POST $U/v2/CreateKey -d '{"name":"myapp"}'
# grant key read/write on bucket
curl -H "$H" -X POST $U/v2/AllowBucketKey \
  -d '{"bucketId":"<bucket-id>","accessKeyId":"<key-id>","permissions":{"read":true,"write":true}}'
```

## Per-app access (boto3)

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
print(s3.get_object(Bucket="myapp", Key="hello.txt")["Body"].read())
```

## Notes

- Garage v2 config notes (see `garage.toml`): `replication_mode` is gone
  (`replication_factor` + `consistency_mode`), `[s3_web]` uses `bind_addr`,
  node capacity in the layout is in bytes, admin API is `/v2/<OperationName>`
  (v1 paths return "no longer supported").
- The image has no ENTRYPOINT: CMD is `["/garage","server"]` — never set
  `command:`/`entrypoint:` on top of it.
- Cloudflare fronts `*.haviv.pro` (orange cloud): fine for API traffic, but
  uploads are limited (~100 MB) and some client user-agents may trip bot rules;
  for big files create a DNS-only subdomain pointing at the origin.
- Named volumes (`fslw8ansy30hxfhffbfseyi0-garage-storage-{meta,data}`) persist
  data across redeploys.
