# opencode-modal-pool-auth

This plugin does both runtime rotation and key onboarding.

- Runtime: direct per-session key injection for Modal requests.
- Login: `opencode auth login -p modal` pushes newly entered Modal keys into the GLM rotator pool.

## Required environment variables

```bash
MODAL_GATEWAY_KEY=<gateway-key>
MODAL_POOL_URL=http://92.5.60.87:4100/modal
MODAL_POOL_MASTER_KEY=<pool-admin-key>
MODAL_BASE_URL=https://api.us-west-2.modal.direct/v1
```

## Behavior

1. User runs `opencode auth login -p modal`
2. Plugin prompts for a new `modalresearch_...` key
3. Plugin posts it to `POST /modal/pool/keys`
4. The pool stores it immediately
5. Runtime requests lease a key per session and call Modal directly
