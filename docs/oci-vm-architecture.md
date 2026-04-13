# OCI VM Architecture — Oracle Cloud Infrastructure Always Free

> **HOST:** `ubuntu@92.5.60.87`
> **SHAPE:** VM.Standard.A1.Flex (4 OCPU, 24 GB RAM, 193 GB boot volume)
> **TIER:** Oracle Cloud Always Free (never expires)

---

## 📊 Hardware & Limits

| Resource | Value | Limit |
|----------|-------|-------|
| **CPU** | 4 OCPU (Ampere A1, ARM64) | 4 OCPU free |
| **RAM** | 24 GB | 24 GB free |
| **Boot Volume** | 193 GB ext4 | 200 GB free (total block storage) |
| **Network** | 40 Gbps max | 10 TB/month outbound free |
| **Public IP** | 92.5.60.87 | 1 ephemeral + 1 reserved free |

---

## 🐳 Docker Services

### Supabase Stack (`/opt/sin-supabase/`)

| Container | Port | Purpose |
|-----------|------|---------|
| `supabase-db` | 5432 (internal) | PostgreSQL 15 |
| `supabase-kong` | 8006, 8444 | API Gateway |
| `supabase-auth` | — | GoTrue (authentication) |
| `supabase-rest` | 3000 (internal) | PostgREST |
| `supabase-studio` | 3004 | Admin UI |
| `supabase-storage` | 5000 (internal) | Storage API |
| `supabase-meta` | 8080 (internal) | Postgres Meta |
| `supabase-pooler` | 6543, 5434 | Supavisor (connection pooling) |
| `supabase-analytics` | 4000 | Logflare |
| `supabase-vector` | — | Vector monitoring |
| `supabase-imgproxy` | 8080 (internal) | Image proxy |
| `supabase-edge-functions` | — | Deno edge runtime |
| `realtime-dev` | — | Realtime subscriptions |

### n8n (`/opt/n8n/`)

| Container | Port | Purpose |
|-----------|------|---------|
| `n8n-n8n-1` | 5678 | Workflow automation engine |

### OpenSIN Neural Bus (`/home/ubuntu/OpenSIN-Neural-Bus/`)

| Container | Port | Purpose |
|-----------|------|---------|
| `opensin-neural-bus-pgvector-1` | 5435 | PgVector database |
| `opensin-neural-bus-nats-1` | 4222, 8222 | NATS message broker |
| `opensin-neural-bus-redis-1` | 6380 | Redis cache |

### sin-room13 (`/opt/sin-room13/`)

| Container | Port | Purpose |
|-----------|------|---------|
| `sin-room13` | 8014 | Task ingestion coordinator |
| `room-04-redis-cache` | 6379 (internal) | Redis cache for Room13 |

### llm-tunnel

| Container | Purpose |
|-----------|---------|
| `llm-tunnel` | Cloudflare cloudflared tunnel for LLM access |

---

## ⚙️ Systemd Services

| Service | Purpose | Binary |
|---------|---------|--------|
| `sin-server.service` | A2A Server runtime | `/opt/sin-control-plane/.../cli.js serve-a2a` |
| `sin-supabase.service` | Supabase metadata plane | `/opt/sin-control-plane/.../cli.js serve-a2a` |
| `runner-cleanup.timer` | Hourly .so file cleanup | `/usr/local/bin/cleanup-runner-libs.sh` |
| `tmp-clean` (cron) | Daily /tmp cleanup | `find /tmp -mtime +7 -delete` |

---

## 🔄 GitHub Actions Runners

| Runner | Location | Org | Status |
|--------|----------|-----|--------|
| `oci-a1flex-arm64` | `/home/ubuntu/actions-runner/` | OpenSIN-AI | Active |
| `oci-a1flex-arm64-2` | `/home/ubuntu/oci-a1flex-arm64-2/` | OpenSIN-AI | Active |

**Known Issue (FIXED):** .NET runners extract `.so` files to `/tmp/` and never clean them up.
- **Fix:** `DOTNET_BUNDLE_EXTRACT_BASE_DIR=/tmp/dotnet-libs` in `.env`
- **Cleanup:** Hourly systemd timer removes stale files

---

## 💾 Storage Architecture

### Local Storage (OCI VM)
| Path | Size | Purpose |
|------|------|---------|
| `/opt/sin-supabase/volumes/db/data` | ~225 MB | PostgreSQL data |
| `/opt/OpenSIN-Code/.git/` | ~363 MB | Git objects |
| `/var/lib/docker/volumes/` | ~135 MB | Docker volumes |
| `/home/ubuntu/.local/lib/python3.12/site-packages/oci` | ~440 MB | OCI SDK |

### GitLab Storage (Infinite, via `/gitlab-storage` skill)
| Project | Repo Prefix | Purpose |
|---------|-------------|---------|
| `oci-vm` | `oci-vm-storage-` | Docker images, DB dumps, system backups |
| `sin-solver` | `sin-solver-logcenter-` | Logs, videos, screenshots, reports |
| `sin-backend` | `sin-backend-storage-` | Backend files, DB dumps |

**Rotation:** Auto-creates new repos at 9 GB per volume (10 GB free limit - 1 GB safety).

---

## 🌐 Network Ports

| Port | Service | Access |
|------|---------|--------|
| 5678 | n8n Web UI | Public |
| 8006 | Supabase Kong HTTP | Public |
| 8444 | Supabase Kong HTTPS | Public |
| 3004 | Supabase Studio | Public |
| 4000 | Supabase Analytics | Public |
| 8014 | sin-room13 | Public |
| 6543 | Supabase Pooler (PgBouncer) | Internal |
| 5434 | Supabase Pooler (Postgres) | Internal |
| 5435 | PgVector | Internal |
| 4222 | NATS | Internal |
| 6380 | Redis | Internal |

---

## 🔧 Maintenance Commands

```bash
# Check disk usage
df -h /
sudo du -xh / 2>/dev/null | sort -rh | head -20

# Check Docker services
sudo docker ps --format 'table {{.Names}}\t{{.Status}}'

# Restart a service
cd /opt/n8n && sudo docker compose up -d
sudo systemctl restart sin-server

# Check runner cleanup logs
cat /var/log/runner-cleanup.log

# Manual .so cleanup
sudo /usr/local/bin/cleanup-runner-libs.sh
```

---

## ⚠️ Known Issues & Fixes

| Issue | Status | Fix |
|-------|--------|-----|
| `/tmp` fills with .so files (179 GB) | ✅ Fixed | `DOTNET_BUNDLE_EXTRACT_BASE_DIR` + systemd timer |
| Docker containers crash on disk full | ✅ Fixed | Hourly cleanup prevents recurrence |
| `haus-netzwerk` network missing | ✅ Fixed | Created with `--subnet=172.20.0.0/16` |
| rsyslog holds deleted file handles | ✅ Fixed | `sudo systemctl restart rsyslog` |
| Runner.Li holds 2TB memfd files | ✅ Fixed | `sudo kill` on stale processes |

---

*Last updated: 2026-04-13*
