-- Populate Supabase with team structure v5
-- Generated: 2026-04-14

-- Team: Team Coding
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Coding', 'team-code', 'A2A-SIN-Zeus', 'Elite-Coder-Flotte fuer Implementation, Testing, Deployment', 'google/antigravity-claude-sonnet-4-6', 'ARRAY['openai/gpt-5.4','qwen/coder-model','google/antigravity-gemini-3.1-pro']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Worker
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Worker', 'team-worker', 'A2A-SIN-Team-Worker', 'Autonome Worker fuer Surveys, Freelancing, Monetarisierung', 'google/antigravity-gemini-3-flash', 'ARRAY['openai/gpt-5.4','qwen/coder-model','nvidia-nim/stepfun-ai/step-3.5-flash']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Infrastructure
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Infrastructure', 'team-infrastructure', 'A2A-SIN-Team-Infrastructure', 'DevOps-Flotte fuer Deployment, CI/CD, Monitoring, Infrastructure', 'openai/gpt-5.4', 'ARRAY['google/antigravity-claude-sonnet-4-6','qwen/coder-model','google/antigravity-gemini-3.1-pro']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Google Apps
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Google Apps', 'team-google-apps', 'A2A-SIN-Google-Apps', 'Google Workspace Integration — Docs, Sheets, Drive, Gmail', 'google/antigravity-gemini-3.1-pro', 'ARRAY['openai/gpt-5.4','qwen/coder-model','google/antigravity-claude-sonnet-4-6']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Apple Apps
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Apple Apps', 'team-apple-apps', 'A2A-SIN-Apple-Apps', 'Apple Ecosystem — macOS Automation, iOS, Shortcuts', 'openai/gpt-5.4', 'ARRAY['google/antigravity-gemini-3-flash','qwen/coder-model']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Apple
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Apple', 'team-apple', 'A2A-SIN-Apple', 'macOS/iOS Automation — Mail, Notes, Calendar, FaceTime, Safari, etc.', 'openai/gpt-5.4', 'ARRAY['google/antigravity-gemini-3-flash','qwen/coder-model']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Social
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Social', 'team-social', 'A2A-SIN-Social', 'Social Media Automation — TikTok, Instagram, X, LinkedIn, Facebook, YouTube', 'google/antigravity-gemini-3.1-pro', 'ARRAY['openai/gpt-5.4','google/antigravity-claude-sonnet-4-6']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Messaging
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Messaging', 'team-messaging', 'A2A-SIN-Messaging', 'Messaging Integration — WhatsApp, Telegram, Signal, Discord, iMessage', 'google/antigravity-gemini-3-flash', 'ARRAY['openai/gpt-5.4','qwen/coder-model']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Forum
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Forum', 'team-forum', 'A2A-SIN-Forum', 'Forum Automation — Reddit, HackerNews, StackOverflow, Quora, DevTo', 'google/antigravity-gemini-3-flash', 'ARRAY['openai/gpt-5.4','qwen/coder-model']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Legal
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Legal', 'team-legal', 'A2A-SIN-Legal', 'Legal Automation — ClaimWriter, Patents, Damages, Compliance, Contract', 'google/antigravity-gemini-3.1-pro', 'ARRAY['openai/gpt-5.4','qwen/coder-model']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Commerce
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Commerce', 'team-commerce', 'A2A-SIN-Commerce', 'Commerce Automation — Shop-Finance, Shop-Logistic, TikTok-Shop, Stripe', 'google/antigravity-gemini-3.1-pro', 'ARRAY['openai/gpt-5.4','google/antigravity-claude-sonnet-4-6']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Community
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Community', 'team-community', 'A2A-SIN-Community', 'Community Management — Discord, WhatsApp, Telegram, YouTube Community', 'google/antigravity-gemini-3-flash', 'ARRAY['openai/gpt-5.4','qwen/coder-model']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Google
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Google', 'team-google', 'A2A-SIN-Google', 'Google Workspace — Google-Apps, Google-Chat, Opal', 'google/antigravity-gemini-3.1-pro', 'ARRAY['openai/gpt-5.4','qwen/coder-model']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Microsoft
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Microsoft', 'team-microsoft', 'A2A-SIN-Microsoft', 'Microsoft 365 — Teams, Outlook, OneDrive, Excel, Word, PowerPoint', 'openai/gpt-5.4', 'ARRAY['google/antigravity-claude-sonnet-4-6','qwen/coder-model']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Research
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Research', 'team-research', 'A2A-SIN-Research', 'Deep Research Agent', 'google/antigravity-gemini-3.1-pro', 'ARRAY['openai/gpt-5.4','google/antigravity-claude-opus-4-6-thinking']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Media ComfyUI
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Media ComfyUI', 'team-media-comfyui', 'A2A-SIN-Media-ComfyUI', 'Media Generation — ImageGen, VideoGen, ComfyUI Workflows', 'google/antigravity-gemini-3.1-pro', 'ARRAY['openai/gpt-5.4','google/antigravity-claude-sonnet-4-6']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Media Music
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Media Music', 'team-media-music', 'A2A-SIN-Media-Music', 'Music Production — Beats, Producer, Singer, Songwriter, Videogen', 'google/antigravity-gemini-3.1-pro', 'ARRAY['openai/gpt-5.4','google/antigravity-claude-sonnet-4-6']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Coding CyberSec
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Coding CyberSec', 'team-coding-cybersec', 'A2A-SIN-Code-CyberSec', 'Security Specialists — BugBounty, Cloudflare, 16x Security-Spezialisten', 'google/antigravity-claude-sonnet-4-6', 'ARRAY['openai/gpt-5.4','google/antigravity-gemini-3.1-pro']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Coding Frontend
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Coding Frontend', 'team-coding-frontend', 'A2A-SIN-Code-Frontend', 'Frontend Specialists — Accessibility, App-Shell, Commerce-UI, Design-Systems', 'google/antigravity-gemini-3.1-pro', 'ARRAY['google/antigravity-claude-sonnet-4-6','openai/gpt-5.4']'
ON CONFLICT (name) DO NOTHING;

-- Team: Team Coding Backend
INSERT INTO teams (id, name, slug, manager, description, primary_model, fallback_models)
SELECT gen_random_uuid(), 'Team Coding Backend', 'team-coding-backend', 'A2A-SIN-Code-Backend', 'Backend Specialists — Server, OracleCloud, Passwordmanager', 'google/antigravity-claude-sonnet-4-6', 'ARRAY['openai/gpt-5.4','google/antigravity-gemini-3.1-pro']'
ON CONFLICT (name) DO NOTHING;
