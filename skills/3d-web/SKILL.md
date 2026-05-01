---
name: 3d-web
description: Integrate ready-made GLB/GLTF 3D assets into websites, webapps, landing pages, and webshops with production-grade web performance, interaction, and fallback behavior.
---

> OpenCode mirror: sourced from `~/.config/opencode/skills/3d-web` and mirrored for OpenCode CLI usage.

# 3D Web

Use this skill when a user wants to place an already-finished 3D asset on a website or webapp — especially a mascot, logo, product model, hero object, or floating chat-style character.

## When to use

- A finished `.glb` or `.gltf` file already exists.
- The goal is **web integration**, not 3D asset creation.
- The page needs interactive 3D behavior:
  - mouse tracking
  - drag rotation
  - hover reaction
  - idle animation
  - click-to-open-chat behavior
  - lightweight character-state behavior (idle / sleep / annoyed / talking)
- The target is one of these:
  - marketing website
  - SaaS webapp
  - webshop / product page
  - floating mascot / chat widget

## Core rule: prefer GLB

For web delivery, prefer:

- **`.glb`** → recommended default
- `.gltf` → acceptable if the asset intentionally ships as multi-file

Why:

- browser-friendly
- supported by modern web 3D stacks
- carries materials / textures / animation cleanly
- easier deployment than `.fbx` or `.obj`

Avoid for normal web integration:

- `.obj` → weak for animation / hierarchy
- `.fbx` → heavier and unnecessarily awkward in browsers

## Preferred web stack

Choose the lightest stack that fits the repo.

### Default

- **Three.js**
- `GLTFLoader`

### If the repo is already React-heavy

- still acceptable to use **plain Three.js inside a React component**
- only choose React Three Fiber when the project already uses it or clearly benefits from it

This skill prefers **plain Three.js + GLTFLoader** as the safest default for existing websites.

## Production integration patterns

### 1. Floating mascot / chat widget

Use when the model should live at the bottom-right corner.

Requirements:

- `position: fixed`
- small canvas footprint
- lazy-load after main content is visible
- click should optionally open chat / support / CTA
- do not block first paint

Good pattern:

- load model only on desktop / large screens first
- keep a static fallback icon for reduced-motion / failure cases
- preserve page interactions around the widget

### 2. Hero mascot / landing visual

Use when the model is part of the hero section.

Requirements:

- non-blocking load
- graceful static fallback poster image
- avoid layout shift
- keep copy readable over / around the canvas

### 3. Product / webshop viewer

Use when the 3D asset is the main product preview.

Requirements:

- drag rotate
- zoom constraints
- stable lighting
- mobile-safe controls
- clear loading state

## Required performance rules

Web 3D must be treated like a performance feature, not a decoration afterthought.

### Hard expectations

- prefer **compressed GLB**
- keep hero/widget assets as small as possible
- lazy-load Three.js and the model when practical
- do not block route transitions
- cap `renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))`
- stop animation loops on unmount
- dispose renderer / geometry / materials / textures on teardown

### Strong recommendations

- target **< 5 MB** for normal mascot/widget assets
- use **Draco compression** for production when possible
- reduce unnecessary polygon counts
- bake materials / textures cleanly before export
- use transparent canvas only when truly needed

### Oversized-asset fallback

If the target host has a strict per-file limit (for example Cloudflare Pages at 25 MiB per file), do **not** ship a giant GLB as one file.

Use one of these strategies:

1. optimize / compress the GLB first
2. host the GLB from object storage / CDN
3. split the GLB into browser-fetched chunks and reconstruct it at runtime

Bundled helper:

```bash
python3 "$HOME/.config/opencode/skills/3d-web/scripts/split_glb_for_web.py" \
  /absolute/path/mascot.glb \
  --output-dir /absolute/path/public/mascot \
  --base-name mascot \
  --chunk-size-mib 24
```

This writes:

- `mascot.manifest.json`
- `mascot.part001.bin`
- `mascot.part002.bin`
- `...`

The browser can then fetch the manifest and parts, rebuild a `Blob`, and load the GLB from an object URL.

### Red flags

- giant GLB files (tens of MB) shipped directly to every visitor
- full-screen autoplay 3D before content becomes visible
- unbounded render loops on hidden tabs / offscreen widgets
- loading 3D on mobile with no gating strategy

## Asset checklist

Before web integration, inspect the asset for:

- named nodes (for example: `Head`, `Eye_L`, `Eye_R`)
- separate eye meshes if eye tracking is desired
- animation clips if blinks / idles already exist
- texture count and total size
- file size and polygon budget

If the asset is too large, say so explicitly and add an optimization step.

## Interaction patterns

### Mouse tracking

Typical implementation ideas:

- convert cursor position to normalized device coordinates
- build a target vector
- rotate head slightly toward the pointer
- drive eye focus more aggressively than head rotation

Useful methods / concepts:

- `lookAt()`
- raycasting (optional, when world-space targeting is needed)
- smoothing / lerp / damping

### Drag rotation

Typical implementation ideas:

- pointer down → start drag state
- pointer move → rotate root model
- pointer up / leave → stop drag state
- clamp extreme X rotation

### Character state machine

Good mascot state set:

- `IDLE`
- `SLEEP`
- `ANNOYED`
- `TALKING`

Typical triggers:

- inactivity timeout → `SLEEP`
- fast mouse speed → `ANNOYED`
- click / chat open / TTS → `TALKING`
- no activity → `IDLE`

### Fake talking without rigging

If the model has no mouth rig, fake talking in code:

- slight model bobbing
- tiny scale pulse
- mild head wobble
- optional blink timing

This is acceptable for mascot widgets and often enough for website UX.

## Minimal Three.js component contract

When building a reusable component, it should:

- accept a `src` for the GLB
- mount into a contained DOM node
- lazily initialize scene / camera / renderer
- support either a direct `.glb` URL or a chunk manifest URL
- support:
  - hover state
  - mouse tracking
  - idle animation
  - click callback
- clean up on unmount
- optionally disable itself on small screens / reduced motion

## Best practices by environment

### Vite / React site

- put the asset in `public/`
- load from a stable public path like `/mascot.glb`
- keep the 3D widget isolated in a reusable component (`Mascot3D.tsx`)
- code-split if the bundle impact is too high

### Next.js / App Router

- client component for the 3D widget
- lazy import the widget where practical
- asset under `public/mascot.glb`

### Static site / plain HTML

- use a fixed DOM container
- import Three.js + `GLTFLoader`
- keep the script self-contained and non-blocking

## Example implementation brief for a coder

Use a `.glb` 3D model.
Render it with Three.js.
Place it fixed in the bottom-right corner like a chat widget.
Enable mouse tracking:

- rotate the head slightly toward the cursor
- have the eyes follow the cursor using `lookAt()`
- let the user drag to rotate the model
- add hover scaling, idle motion, and a talking state
  Optimize for performance:
- lazy-load the model
- cap DPR
- dispose resources on unmount
- use Draco compression for production assets

## Validation checklist

Before calling the work done, verify:

- the page still loads and remains usable without the model
- the model appears in the intended location
- the widget does not cover critical CTAs or nav
- drag rotation works
- mouse tracking works
- mobile does not choke on the asset
- there is a fallback when WebGL or model loading fails
- Lighthouse / runtime performance is still acceptable

## Completion standard

This skill is successful when the 3D asset is:

- integrated cleanly into the real web UI
- interactive and stable
- performance-aware
- easy for future coders to reuse
- not dependent on Blender edits unless the asset truly requires them
