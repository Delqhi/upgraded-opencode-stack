# OCI VM Architecture — Oracle Cloud Infrastructure Always Free

> **HOST:** `ubuntu@92.5.60.87`
> **SHAPE:** VM.Standard.A1.Flex (4 OCPU, 24 GB RAM, 193 GB boot volume)
> **TIER:** Oracle Cloud Always Free (never expires)

---

## 📊 Hardware & Limits

| Resource        | Value                     | Limit                             |
| --------------- | ------------------------- | --------------------------------- |
| **CPU**         | 4 OCPU (Ampere A1, ARM64) | 4 OCPU free                       |
| **RAM**         | 24 GB                     | 24 GB free                        |
| **Boot Volume** | 193 GB ext4               | 200 GB free (total block storage) |
| **Network**     | 40 Gbps max               | 10 TB/month outbound free         |
| **Public IP**   | 92.5.60.87                | 1 ephemeral + 1 reserved free     |

---

## 🐳 Docker Services

### Supabase Stack (`/opt/sin-supabase/`)

| Container                 | Port            | Purpose                        |
| ------------------------- | --------------- | ------------------------------ |
| `supabase-db`             | 5432 (internal) | PostgreSQL 15                  |
| `supabase-kong`           | 8006, 8444      | API Gateway                    |
| `supabase-auth`           | —               | GoTrue (authentication)        |
| `supabase-rest`           | 3000 (internal) | PostgREST                      |
| `supabase-studio`         | 3004            | Admin UI                       |
| `supabase-storage`        | 5000 (internal) | Storage API                    |
| `supabase-meta`           | 8080 (internal) | Postgres Meta                  |
| `supabase-pooler`         | 6543, 5434      | Supavisor (connection pooling) |
| `supabase-analytics`      | 4000            | Logflare                       |
| `supabase-vector`         | —               | Vector monitoring              |
| `supabase-imgproxy`       | 8080 (internal) | Image proxy                    |
| `supabase-edge-functions` | —               | Deno edge runtime              |
| `realtime-dev`            | —               | Realtime subscriptions         |

### n8n (`/opt/n8n/`)

| Container   | Port | Purpose                    |
| ----------- | ---- | -------------------------- |
| `n8n-n8n-1` | 5678 | Workflow automation engine |

### OpenSIN Neural Bus (`/home/ubuntu/OpenSIN-Neural-Bus/`)

| Container                       | Port       | Purpose             |
| ------------------------------- | ---------- | ------------------- |
| `opensin-neural-bus-pgvector-1` | 5435       | PgVector database   |
| `opensin-neural-bus-nats-1`     | 4222, 8222 | NATS message broker |
| `opensin-neural-bus-redis-1`    | 6380       | Redis cache         |

### sin-room13 (`/opt/sin-room13/`)

| Container             | Port            | Purpose                    |
| --------------------- | --------------- | -------------------------- |
| `sin-room13`          | 8014            | Task ingestion coordinator |
| `room-04-redis-cache` | 6379 (internal) | Redis cache for Room13     |

### llm-tunnel

| Container    | Purpose                                      |
| ------------ | -------------------------------------------- |
| `llm-tunnel` | Cloudflare cloudflared tunnel for LLM access |

---

## ⚙️ Systemd Services

| Service                | Purpose                 | Binary                                        |
| ---------------------- | ----------------------- | --------------------------------------------- |
| `sin-server.service`   | A2A Server runtime      | `/opt/sin-control-plane/.../cli.js serve-a2a` |
| `sin-supabase.service` | Supabase metadata plane | `/opt/sin-control-plane/.../cli.js serve-a2a` |
| `runner-cleanup.timer` | Hourly .so file cleanup | `/usr/local/bin/cleanup-runner-libs.sh`       |
| `tmp-clean` (cron)     | Daily /tmp cleanup      | `find /tmp -mtime +7 -delete`                 |

---

## 🔄 GitHub Actions Runners

| Runner               | Location                           | Org        | Status |
| -------------------- | ---------------------------------- | ---------- | ------ |
| `oci-a1flex-arm64`   | `/home/ubuntu/actions-runner/`     | OpenSIN-AI | Active |
| `oci-a1flex-arm64-2` | `/home/ubuntu/oci-a1flex-arm64-2/` | OpenSIN-AI | Active |

**Known Issue (FIXED):** .NET runners extract `.so` files to `/tmp/` and never clean them up.

- **Fix:** `DOTNET_BUNDLE_EXTRACT_BASE_DIR=/tmp/dotnet-libs` in `.env`
- **Cleanup:** Hourly systemd timer removes stale files

---

## 💾 Storage Architecture

### Local Storage (OCI VM)

| Path                                                   | Size    | Purpose         |
| ------------------------------------------------------ | ------- | --------------- |
| `/opt/sin-supabase/volumes/db/data`                    | ~225 MB | PostgreSQL data |
| `/opt/OpenSIN-Code/.git/`                              | ~363 MB | Git objects     |
| `/var/lib/docker/volumes/`                             | ~135 MB | Docker volumes  |
| `/home/ubuntu/.local/lib/python3.12/site-packages/oci` | ~440 MB | OCI SDK         |

### GitLab Storage (Infinite, via `/gitlab-storage` skill)

| Project       | Repo Prefix             | Purpose                                 |
| ------------- | ----------------------- | --------------------------------------- |
| `oci-vm`      | `oci-vm-storage-`       | Docker images, DB dumps, system backups |
| `sin-solver`  | `sin-solver-logcenter-` | Logs, videos, screenshots, reports      |
| `sin-backend` | `sin-backend-storage-`  | Backend files, DB dumps                 |

**Rotation:** Auto-creates new repos at 9 GB per volume (10 GB free limit - 1 GB safety).

---

## 🌐 Network Ports

| Port | Service                     | Access   |
| ---- | --------------------------- | -------- |
| 5678 | n8n Web UI                  | Public   |
| 8006 | Supabase Kong HTTP          | Public   |
| 8444 | Supabase Kong HTTPS         | Public   |
| 3004 | Supabase Studio             | Public   |
| 4000 | Supabase Analytics          | Public   |
| 8014 | sin-room13                  | Public   |
| 6543 | Supabase Pooler (PgBouncer) | Internal |
| 5434 | Supabase Pooler (Postgres)  | Internal |
| 5435 | PgVector                    | Internal |
| 4222 | NATS                        | Internal |
| 6380 | Redis                       | Internal |

---

## 🗂️ Related GitHub Repos (OpenSIN-AI org)

OCI VM components are spread across multiple repos:

| Repo                                                                                          | Purpose                           | OCI VM Component                  |
| --------------------------------------------------------------------------------------------- | --------------------------------- | --------------------------------- |
| [`OpenSIN-AI/OpenSIN-backend`](https://github.com/OpenSIN-AI/OpenSIN-backend)                 | Backend + A2A fleet control plane | sin-server, sin-supabase services |
| [`OpenSIN-AI/OpenSIN-Neural-Bus`](https://github.com/OpenSIN-AI/OpenSIN-Neural-Bus)           | Event-Driven Nervous System       | pgvector + NATS + Redis stack     |
| [`OpenSIN-AI/Team-SIN-Infrastructure`](https://github.com/OpenSIN-AI/Team-SIN-Infrastructure) | Infrastructure team               | VM management, deployment         |
| [`OpenSIN-AI/Infra-SIN-Dev-Setup`](https://github.com/OpenSIN-AI/Infra-SIN-Dev-Setup)         | Dev Environment Setup             | Initial VM provisioning           |
| [`OpenSIN-AI/sin-github-action`](https://github.com/OpenSIN-AI/sin-github-action)             | Self-hosted CI/CD                 | GitHub Actions Runners            |
| [`OpenSIN-AI/Core-SIN-Control-Plane`](https://github.com/OpenSIN-AI/Core-SIN-Control-Plane)   | Doctor/Preflight/Eval             | Health checks, preflight          |
| [`OpenSIN-Code/Infra-SIN-OpenCode-Stack`](https://github.com/OpenSIN-Code/Infra-SIN-OpenCode-Stack)         | OpenCode Stack (local)            | Skills, plugins, configs          |

---

## 🔧 Maintenance Commands

```bash
# Check disk usage (live)
df -h /

# All 6 coder agents healthy?
curl -s http://localhost:7860/health && curl -s http://localhost:7861/health && curl -s http://localhost:7862/health && curl -s http://localhost:7863/health && curl -s http://localhost:7864/health && curl -s http://localhost:7865/health

# All 5 protection timers active?
systemctl list-timers | grep -E "runner-cleanup|oci-space-guardian|oci-emergency-disk-guard|oci-log-rotation|oci-disk-self-test"

# Check Docker services
sudo docker ps --format 'table {{.Names}}\t{{.Status}}'

# Restart a service
cd /opt/n8n && sudo docker compose up -d
sudo systemctl restart sin-server

# Run manual .so cleanup (Python glob, not regex)
sudo /usr/local/bin/cleanup-runner-libs.sh

# Run space guardian manually
sudo /usr/local/bin/oci-space-guardian.sh

# Check emergency guard last-stop reason
cat /var/lib/oci-emergency-disk-guard/last-stop.txt 2>/dev/null || echo "No emergency stop recorded"

# Check self-test last result
sudo /usr/local/bin/oci-disk-self-test.sh

# See recent journald entries for an agent
sudo journalctl -u a2a-sin-code-backend -n 20 --no-pager
```

---

## ⚠️ Known Issues & Fixes

| Issue                                              | Status   | Fix                                              |
| -------------------------------------------------- | -------- | ------------------------------------------------ |
| `/tmp` fills with .so files (179 GB) — BUG-OCI-001 | ✅ Fixed | 5-layer protection stack (see below)             |
| Docker containers crash on disk full               | ✅ Fixed | `oci-space-guardian.timer` prunes Docker at ≥80% |
| `haus-netzwerk` network missing                    | ✅ Fixed | Created with `--subnet=172.20.0.0/16`            |
| rsyslog holds deleted file handles                 | ✅ Fixed | `sudo systemctl restart rsyslog`                 |
| Runner.Li holds 2TB memfd files                    | ✅ Fixed | `sudo kill` on stale processes                   |
| Agent `/health` returns 404 (Gradio shadowing)     | ✅ Fixed | FastAPI routes registered before Gradio mount    |
| `is_healthy()` leaks .so files per call            | ✅ Fixed | Changed to `shutil.which("opencode")`            |

---

## 🚨 BUG-OCI-001: OCI VM Disk Full Prevention (2026-04-16)

> **Incident Date:** 2026-04-16 — OCI VM `92.5.60.87` went 100% disk full. All 6 coder agents died.
> **Root Cause:** `is_healthy()` called `subprocess.run(["opencode", "--version"])` which leaked ~4.4 MB `.so` files per call into `/tmp/`. Python's `glob.glob(r"/tmp/.*.so")` was a **broken regex** (`.` not escaped, so nothing matched).

### 5-Layer Protection Stack (fully deployed)

| Layer                  | Timer        | Script                        | Action                                            |
| ---------------------- | ------------ | ----------------------------- | ------------------------------------------------- |
| **1. Runner Cleanup**  | every 5 min  | `cleanup-runner-libs.sh`      | Python glob clean `/tmp/.*.so` >10min             |
| **2. Space Guardian**  | every 1 hour | `oci-space-guardian.sh`       | Prune caches+Docker at ≥80%, escalate at ≥85%     |
| **3. Emergency Guard** | every 5 min  | `oci-emergency-disk-guard.sh` | Auto-stop all 6 agents if disk stays ≥85%         |
| **4. Log Rotation**    | daily        | `oci-log-rotation.sh`         | journald 200MB max, syslog vacuum                 |
| **5. Self-Test**       | daily 03:00  | `oci-disk-self-test.sh`       | 27-point verification — alerts if any check fails |

**systemd drop-ins** on all 6 agents (`/etc/systemd/system/a2a-sin-code-*.service.d/hardening.conf`):

- `StartLimitIntervalSec=300`, `StartLimitBurst=3` — crash storm brake
- `Restart=on-failure`, `RestartSec=30`
- `ExecStartPre=-/usr/local/bin/cleanup-runner-libs.sh`

### Quick Verification Commands

```bash
# Disk + agents + timers in one shot
df -h / && systemctl is-active a2a-sin-code-* && systemctl list-timers | grep oci

# Run 27-point self-test
sudo /usr/local/bin/oci-disk-self-test.sh

# Emergency: stop all 6 agents
sudo systemctl stop a2a-sin-code-backend a2a-sin-code-command a2a-sin-code-frontend a2a-sin-code-fullstack a2a-sin-code-plugin a2a-sin-code-tool

# Emergency: restart all 6 agents
sudo systemctl start a2a-sin-code-backend a2a-sin-code-command a2a-sin-code-frontend a2a-sin-code-fullstack a2a-sin-code-plugin a2a-sin-code-tool
```

**Source-controlled at:** [`OpenSIN-AI/Infra-SIN-Dev-Setup`](https://github.com/OpenSIN-AI/Infra-SIN-Dev-Setup) — `scripts/` + `systemd/`

---

_Last updated: 2026-04-17 — BUG-OCI-001 hardening stack integrated_
