# OpenSIN-AI — Shopify Design System

> E-commerce platform meets AI orchestration. Dark-first cinematic, neon green accent, ultra-light display type.

**Style**: Dark-first cinematic, neon green accent, ultra-light display typography  
**Use for**: OpenSIN-AI websites, webapps, SaaS marketing, product showcases

---

## 1. Visual Theme & Atmosphere

| Property           | Value                                                                                                            |
| ------------------ | ---------------------------------------------------------------------------------------------------------------- |
| Mood               | Premium, cinematic, confident                                                                                    |
| Density            | Spacious, full-bleed imagery                                                                                     |
| Design philosophy  | Dark surfaces first, green accent highlights, monumental type scale                                              |
| Primary surfaces   | Deep black (#0a0a0a) and forest green (#004c3f) undertones                                                       |
| Secondary surfaces | Card surfaces with subtle border and green glow                                                                  |
| Philosophy         | Let product and content breathe. Dark canvas, neon-green call-to-action, massive display type for hero sections. |

---

## 2. Color Palette & Roles

### Primary Colors

| Semantic Name      | Hex       | Role                                             |
| ------------------ | --------- | ------------------------------------------------ |
| `--background`     | `#0a0a0a` | Page background, primary canvas                  |
| `--surface-1`      | `#141414` | Elevated surfaces, cards                         |
| `--surface-2`      | `#1a1a1a` | Secondary cards, modals                          |
| `--surface-3`      | `#222222` | Input backgrounds, tertiary surfaces             |
| `--accent`         | `#008060` | Shopify green — primary CTA, links, focus states |
| `--accent-hover`   | `#006e52` | Accent hover state                               |
| `--accent-glow`    | `#00ff9e` | Neon green glow for hero sections, badges        |
| `--text-primary`   | `#f5f5f5` | Primary text, headings                           |
| `--text-secondary` | `#a0a0a0` | Secondary text, descriptions, labels             |
| `--text-muted`     | `#666666` | Muted text, placeholders, disabled               |
| `--border`         | `#2a2a2a` | Borders, dividers                                |
| `--border-accent`  | `#008060` | Active state borders, focus rings                |
| `--error`          | `#e04f5f` | Error states, destructive actions                |
| `--success`        | `#00cc88` | Success states, completed actions                |
| `--warning`        | `#ffcc00` | Warning states, attention needed                 |

### OpenSIN Brand Extensions

| Semantic Name      | Hex       | Role                                 |
| ------------------ | --------- | ------------------------------------ |
| `--opensin-blue`   | `#0066ff` | AI/coding features, agent indicators |
| `--opensin-purple` | `#8b5cf6` | Premium features, A2A ecosystem      |
| `--opensin-cyan`   | `#00d4ff` | Live status, real-time indicators    |

---

## 3. Typography Rules

### Font Families

| Usage           | Font                          | Weight                |
| --------------- | ----------------------------- | --------------------- |
| Display / Hero  | `Inter`, system-ui            | 100-200 (ultra-light) |
| Headings        | `Inter`, system-ui            | 500-600               |
| Body            | `Inter`, system-ui            | 400                   |
| Code / Terminal | `JetBrains Mono`, `Fira Code` | 400                   |
| Navigation      | `Inter`, system-ui            | 500                   |

### Type Scale

| Level       | Size | Weight | Line Height | Use                           |
| ----------- | ---- | ------ | ----------- | ----------------------------- |
| `display-1` | 72px | 100    | 1.1         | Hero headlines, landing pages |
| `display-2` | 56px | 100    | 1.15        | Section hero                  |
| `h1`        | 48px | 500    | 1.2         | Page titles                   |
| `h2`        | 36px | 500    | 1.25        | Section titles                |
| `h3`        | 28px | 500    | 1.3         | Subsections                   |
| `h4`        | 22px | 500    | 1.35        | Card titles                   |
| `body-lg`   | 18px | 400    | 1.6         | Lead paragraphs               |
| `body`      | 16px | 400    | 1.6         | Body text                     |
| `body-sm`   | 14px | 400    | 1.5         | Captions, labels              |
| `code`      | 14px | 400    | 1.5         | Code blocks, terminal         |
| `button`    | 16px | 500    | 1.0         | Button text                   |
| `badge`     | 12px | 500    | 1.0         | Status badges, tags           |

### Typography Rules

- Hero sections use **ultra-light weight** (100-200) at **massive scale** (72px+)
- Body text is never smaller than 16px
- Code blocks use monospace with subtle background
- All text on dark surfaces uses `#f5f5f5` minimum for accessibility
- Links are accent green with underline on hover

---

## 4. Component Stylings

### Buttons

| Variant     | Background  | Text      | Border              | Hover     | Radius |
| ----------- | ----------- | --------- | ------------------- | --------- | ------ |
| Primary     | `#008060`   | `#ffffff` | none                | `#006e52` | 8px    |
| Secondary   | transparent | `#f5f5f5` | `1px solid #2a2a2a` | `#222222` | 8px    |
| Ghost       | transparent | `#a0a0a0` | none                | `#f5f5f5` | 8px    |
| Destructive | `#e04f5f`   | `#ffffff` | none                | `#c93e4d` | 8px    |
| Icon        | transparent | `#a0a0a0` | none                | `#f5f5f5` | 8px    |

```css
.btn-primary {
  background: #008060;
  color: #ffffff;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  font-size: 16px;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-primary:hover {
  background: #006e52;
}

.btn-secondary {
  background: transparent;
  color: #f5f5f5;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  font-size: 16px;
  border: 1px solid #2a2a2a;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-secondary:hover {
  background: #222222;
  border-color: #3a3a3a;
}
```

### Cards

```css
.card {
  background: #141414;
  border: 1px solid #2a2a2a;
  border-radius: 12px;
  padding: 24px;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}
.card:hover {
  border-color: #008060;
  box-shadow: 0 0 20px rgba(0, 128, 96, 0.1);
}
```

### Input Fields

```css
.input {
  background: #222222;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 12px 16px;
  color: #f5f5f5;
  font-size: 16px;
  font-family: inherit;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}
.input:focus {
  outline: none;
  border-color: #008060;
  box-shadow: 0 0 0 3px rgba(0, 128, 96, 0.15);
}
.input::placeholder {
  color: #666666;
}
```

### Navigation

- Top navigation: sticky, backdrop-blur, dark translucent background
- Active nav items: green left border + green text
- Hover: text color shifts from `#a0a0a0` to `#f5f5f5`
- Logo: white text, Inter 600, 20px

```css
.nav {
  position: sticky;
  top: 0;
  backdrop-filter: blur(12px);
  background: rgba(10, 10, 10, 0.8);
  border-bottom: 1px solid #2a2a2a;
  z-index: 100;
}
.nav-link {
  color: #a0a0a0;
  text-decoration: none;
  padding: 8px 16px;
  font-weight: 500;
  transition: color 0.2s;
}
.nav-link:hover {
  color: #f5f5f5;
}
.nav-link.active {
  color: #008060;
  border-left: 2px solid #008060;
}
```

### Badges / Tags

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(0, 128, 96, 0.15);
  color: #00ff9e;
  border: 1px solid rgba(0, 128, 96, 0.3);
}
.badge-blue {
  background: rgba(0, 102, 255, 0.15);
  color: #66b3ff;
  border-color: rgba(0, 102, 255, 0.3);
}
.badge-purple {
  background: rgba(139, 92, 246, 0.15);
  color: #c4b5fd;
  border-color: rgba(139, 92, 246, 0.3);
}
```

---

## 5. Layout Principles

| Property              | Value                                                               |
| --------------------- | ------------------------------------------------------------------- |
| Max content width     | 1200px                                                              |
| Grid columns          | 12 (desktop), 4 (tablet), 1 (mobile)                                |
| Spacing scale         | 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px, 96px, 128px           |
| Section padding       | 96px vertical on desktop, 64px on mobile                            |
| Card gap              | 24px grid gap                                                       |
| Container padding     | 24px horizontal on mobile, 48px on desktop                          |
| Whitespace philosophy | Generous vertical spacing between sections, tight within components |

---

## 6. Depth & Elevation

| Level      | Shadow                         | Use                        |
| ---------- | ------------------------------ | -------------------------- |
| `flat`     | none                           | Default surfaces           |
| `raised`   | `0 2px 8px rgba(0,0,0,0.3)`    | Hovered cards              |
| `elevated` | `0 4px 16px rgba(0,0,0,0.4)`   | Dropdowns, popovers        |
| `modal`    | `0 8px 32px rgba(0,0,0,0.5)`   | Modals, dialogs            |
| `glow`     | `0 0 20px rgba(0,128,96,0.15)` | Accent hover, focus states |

---

## 7. Do's and Don'ts

### Do

- ✅ Use dark surfaces as the primary canvas
- ✅ Reserve neon green (`#00ff9e`) for critical actions only
- ✅ Use ultra-light display type (100-200) for hero headlines
- ✅ Full-bleed imagery in hero sections
- ✅ Generous whitespace between sections (96px+)
- ✅ Subtle green border glow on card hover
- ✅ Monospace code blocks with dark background

### Don't

- ❌ Use white backgrounds for primary pages (dark-first design)
- ❌ Use multiple accent colors in the same section
- ❌ Use heavy font weights (>500) for headings
- ❌ Crowd hero sections with too many CTAs (max 2)
- ❌ Use sharp corners (minimum 8px border-radius)
- ❌ Use light text on light backgrounds (accessibility)

---

## 8. Responsive Behavior

| Breakpoint | Width   | Changes                                        |
| ---------- | ------- | ---------------------------------------------- |
| `xl`       | 1440px+ | 12-column grid, 48px horizontal padding        |
| `lg`       | 1024px  | 8-column grid, 32px padding                    |
| `md`       | 768px   | 4-column grid, 24px padding, stacked nav       |
| `sm`       | 640px   | 1-column, mobile nav drawer                    |
| `xs`       | 480px   | Touch targets 44px minimum, reduced type scale |

- Hero display text scales from 72px → 48px on mobile
- Navigation collapses to hamburger menu at 768px
- Cards stack to single column at 640px
- Touch targets minimum 44x44px on mobile

---

## 9. OpenSIN-AI Integration

This design system is adapted for the **OpenSIN-AI** ecosystem:

| OpenSIN Component       | Design Token                                     | Usage                          |
| ----------------------- | ------------------------------------------------ | ------------------------------ |
| **Agent Cards**         | Card with green hover glow                       | Agent listings in dashboard    |
| **Status Indicators**   | `--opensin-cyan` for live, `--accent` for active | Real-time agent status         |
| **Terminal/CLI**        | JetBrains Mono on `#141414` background           | Code examples, terminal output |
| **A2A Ecosystem Badge** | `--opensin-purple` badge                         | A2A agent integrations         |
| **Token Pool Status**   | `--success` / `--warning` / `--error`            | Token pool health indicators   |
| **Hero Sections**       | `display-1` at 72px, ultra-light                 | Landing pages for each agent   |
| **Navigation**          | Sticky, backdrop-blur dark                       | All OpenSIN webapps            |

### Quick Color Reference

```
Background:  #0a0a0a
Surface:     #141414
Accent:      #008060
Neon:        #00ff9e
Text:        #f5f5f5
Muted:       #666666
Border:      #2a2a2a
OpenSIN:     #0066ff (blue) / #8b5cf6 (purple) / #00d4ff (cyan)
```

### Agent Prompt Guide

> "Build a dark-first landing page with Shopify-style cinematic design. Use #0a0a0a background, #008060 green accent, ultra-light Inter 100 for hero text at 72px. Cards with #141414 background, subtle #2a2a2a border, green glow on hover. Navigation sticky with backdrop-blur. Full responsive with mobile drawer."
