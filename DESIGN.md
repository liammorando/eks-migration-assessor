# EKS Migration Assessor — Design System

*Apple-inspired design language for a developer-first migration readiness tool*

---

## Design Philosophy

> **"Design is not just what it looks like and feels like. Design is how it works."** — Steve Jobs

This tool embodies three core principles:

| Principle | Implementation |
|-----------|----------------|
| **Clarity** | Every element serves a purpose; no visual noise |
| **Deference** | UI gets out of the way; content and data take center stage |
| **Depth** | Layered information architecture — scan → explore → act |

---

## Color System

### Light Mode
```css
:root {
  --primary: #0066CC;           /* System Blue */
  --primary-hover: #0051A8;
  --primary-light: #E8F0FE;
  
  --success: #30A14E;           /* System Green */
  --success-light: #E6F4EA;
  
  --warning: #F9A825;           /* System Yellow */
  --warning-light: #FEF7E0;
  
  --danger: #DE3C2C;            /* System Red */
  --danger-light: #FCE8E6;
  
  --bg-primary: #FFFFFF;
  --bg-secondary: #F8F9FA;
  --bg-tertiary: #EEF1F4;
  
  --text-primary: #1D1D1F;
  --text-secondary: #6E6E73;
  --text-tertiary: #98989D;
  
  --border: #D2D2D7;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg: 0 12px 32px rgba(0,0,0,0.12);
  
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-full: 9999px;
}
```

### Dark Mode
```css
@media (prefers-color-scheme: dark) {
  :root {
    --primary: #64B5F6;
    --primary-hover: #90CAF9;
    --primary-light: #0D1B2A;
    
    --success: #81C784;
    --success-light: #1B3A1B;
    
    --warning: #FFB74D;
    --warning-light: #3A2E0A;
    
    --danger: #EF5350;
    --danger-light: #3A1515;
    
    --bg-primary: #1D1D1F;
    --bg-secondary: #1A1A1C;
    --bg-tertiary: #2C2C2E;
    
    --text-primary: #FFFFFF;
    --text-secondary: #EBEBF599;
    --text-tertiary: #EBEBF54D;
    
    --border: #38383A;
  }
}
```

### Severity Palette
| Severity | Color | Usage |
|----------|-------|-------|
| Critical | `#DE3C2C` | Immediate blockers |
| High | `#F9A825` | Significant risk |
| Medium | `#0066CC` | Notable concern |
| Low | `#30A14E` | Minor improvement |
| Info | `#6E6E73` | Informational |

---

## Typography

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", 
             "Helvetica Neue", Helvetica, Arial, sans-serif;
```

### Type Scale
| Style | Size | Weight | Line Height | Tracking | Usage |
|-------|------|--------|-------------|----------|-------|
| **Large Title** | 34px | 700 | 41px | +0.37px | Page titles |
| **Title 1** | 28px | 700 | 34px | +0.36px | Section headers |
| **Title 2** | 22px | 600 | 28px | +0.38px | Card titles |
| **Title 3** | 20px | 600 | 25px | +0.38px | Subsection headers |
| **Headline** | 17px | 600 | 22px | -0.43px | Emphasized body |
| **Body** | 17px | 400 | 22px | -0.43px | Primary text |
| **Callout** | 16px | 400 | 21px | -0.32px | Secondary text |
| **Subheadline** | 15px | 400 | 20px | -0.24px | Tertiary text |
| **Footnote** | 13px | 400 | 18px | -0.08px | Metadata |
| **Caption 1** | 12px | 400 | 16px | 0px | Labels, hints |
| **Caption 2** | 11px | 400 | 13px | +0.07px | Fine print |

---

## Spacing System

### Base Unit: 4px
```css
--space-1: 4px;    /* 1 unit */
--space-2: 8px;    /* 2 units */
--space-3: 12px;   /* 3 units */
--space-4: 16px;   /* 4 units */
--space-5: 20px;   /* 5 units */
--space-6: 24px;   /* 6 units */
--space-8: 32px;   /* 8 units */
--space-10: 40px;  /* 10 units */
--space-12: 48px;  /* 12 units */
--space-16: 64px;  /* 16 units */
```

### Layout Guidelines
- **Page padding**: `--space-6` (24px) mobile, `--space-8` (32px) desktop
- **Card padding**: `--space-4` (16px) compact, `--space-5` (20px) comfortable
- **Component gap**: `--space-3` (12px) tight, `--space-4` (16px) normal
- **Section gap**: `--space-8` (32px) standard, `--space-12` (48px) major

---

## Component Library

### 1. Button

#### Primary
```css
.btn-primary {
  background: var(--primary);
  color: #FFFFFF;
  border: none;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 600;
  padding: 10px 20px;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-sm);
}

.btn-primary:hover {
  background: var(--primary-hover);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.btn-primary:active {
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}
```

#### Secondary
```css
.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 500;
  padding: 10px 20px;
  transition: all 0.15s ease;
}

.btn-secondary:hover {
  background: var(--border);
}
```

#### Destructive
```css
.btn-destructive {
  background: var(--danger-light);
  color: var(--danger);
  border: none;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 500;
  padding: 10px 20px;
}

.btn-destructive:hover {
  background: var(--danger);
  color: #FFFFFF;
}
```

### 2. Input Field

```css
.input-field {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 400;
  color: var(--text-primary);
  padding: 10px 14px;
  width: 100%;
  transition: all 0.15s ease;
}

.input-field:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--primary-light);
}

.input-field::placeholder {
  color: var(--text-tertiary);
}

.input-field:disabled {
  background: var(--bg-secondary);
  color: var(--text-tertiary);
  cursor: not-allowed;
}
```

#### With Label
```html
<div class="input-group">
  <label class="input-label">Ollama Host</label>
  <input type="text" class="input-field" placeholder="http://localhost:11434" />
  <p class="input-hint">API URL for local Ollama instance</p>
</div>
```

```css
.input-group { margin-bottom: var(--space-4); }
.input-label { 
  display: block; 
  font-size: 13px; 
  font-weight: 500; 
  color: var(--text-primary); 
  margin-bottom: var(--space-1); 
}
.input-hint { 
  font-size: 11px; 
  color: var(--text-tertiary); 
  margin-top: var(--space-1); 
}
```

### 3. Card

```css
.card {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--primary);
}

.card-compact { padding: var(--space-4); }
.card-comfortable { padding: var(--space-6); }
```

### 4. Metric Card

```css
.metric-card {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
}

.metric-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--primary);
  line-height: 1.1;
}

.metric-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
```

### 5. Badge / Pill

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
}

.badge-critical { background: var(--danger-light); color: var(--danger); }
.badge-high { background: var(--warning-light); color: #8A6B00; }
.badge-medium { background: var(--primary-light); color: var(--primary); }
.badge-low { background: var(--success-light); color: var(--success); }
.badge-info { background: var(--bg-tertiary); color: var(--text-secondary); }
```

### 6. Finding Card

```css
.finding-card {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  margin-bottom: var(--space-3);
  position: relative;
  transition: all 0.2s ease;
}

.finding-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--primary);
}

.finding-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  border-radius: var(--radius-md) 0 0 var(--radius-md);
}

.finding-critical::before { background: var(--danger); }
.finding-high::before { background: var(--warning); }
.finding-medium::before { background: var(--primary); }
.finding-low::before { background: var(--success); }
.finding-info::before { background: var(--text-tertiary); }
```

### 7. Phase Card (Migration Plan)

```css
.phase-card {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  margin-bottom: var(--space-4);
}

.phase-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
}

.phase-badge {
  background: var(--primary-light);
  color: var(--primary);
  padding: 4px 12px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
}

.phase-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  flex: 1;
}

.effort-badge {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 500;
}
```

### 8. Sidebar Section

```css
.sidebar-section {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-4) var(--space-5);
  margin-bottom: var(--space-3);
}

.sidebar-section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
  margin-bottom: var(--space-3);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--border);
}
```

### 9. Language Selector

```css
.lang-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.lang-btn {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.lang-btn.active {
  background: var(--primary);
  color: #FFFFFF;
  border-color: var(--primary);
}

.lang-btn:not(.active):hover {
  background: var(--bg-tertiary);
  border-color: var(--primary);
}
```

### 10. Status Indicator

```css
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
}

.status-connected {
  background: var(--success-light);
  color: var(--success);
}

.status-disconnected {
  background: var(--danger-light);
  color: var(--danger);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}
```

### 11. Code Block

```css
.code-block {
  background: #1E1E1E;
  color: #D4D4D4;
  border: none;
  border-radius: var(--radius-md);
  font-family: "SF Mono", "Fira Code", monospace;
  font-size: 12px;
  line-height: 1.6;
  padding: var(--space-4);
  overflow-x: auto;
}

.code-block.light {
  background: #F5F5F5;
  color: #1D1D1F;
}
```

### 12. Empty State

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-12) var(--space-6);
  text-align: center;
  color: var(--text-secondary);
}

.empty-state-icon {
  font-size: 48px;
  margin-bottom: var(--space-4);
  opacity: 0.5;
}

.empty-state-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.empty-state-message {
  font-size: 15px;
  max-width: 280px;
  line-height: 1.4;
}
```

---

## Layout Patterns

### Page Structure
```html
<div class="page">
  <header class="app-header">
    <div>
      <h1 class="app-title">Page Title</h1>
      <p class="app-subtitle">Descriptive subtitle</p>
    </div>
    <div class="header-actions">
      <!-- Primary actions -->
    </div>
  </header>
  
  <main class="app-main">
    <div class="content-grid">
      <!-- Primary content -->
      <section class="primary-content">
        <!-- Metrics row -->
        <div class="metrics-row">
          <div class="metric-card">...</div>
          <div class="metric-card">...</div>
          <div class="metric-card">...</div>
        </div>
        
        <!-- Tabs -->
        <div class="tabs-container">...</div>
      </section>
    </div>
  </main>
  
  <footer class="app-footer">
    <p>Footer text</p>
  </footer>
</div>
```

### Grid System
```css
.content-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-6);
}

@media (min-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr 320px; /* Main + Sidebar */
  }
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

@media (max-width: 768px) {
  .metrics-row {
    grid-template-columns: 1fr;
  }
}
```

---

## Motion & Animation

### Timing Functions
```css
--ease-standard: cubic-bezier(0.4, 0.0, 0.2, 1);
--ease-decelerate: cubic-bezier(0.0, 0.0, 0.2, 1);
--ease-accelerate: cubic-bezier(0.4, 0.0, 1, 1);
--ease-sharp: cubic-bezier(0.4, 0.0, 0.6, 1);
```

### Durations
| Duration | Usage |
|----------|-------|
| 100ms | Micro-interactions (hover, focus) |
| 150ms | Standard transitions |
| 200ms | Card hover, drawer slide |
| 300ms | Modal, panel transitions |
| 400ms | Page transitions |

### Key Animations
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Usage */
.animate-fade-in { animation: fadeIn 150ms var(--ease-decelerate); }
.animate-slide-up { animation: slideUp 200ms var(--ease-decelerate); }
.animate-scale-in { animation: scaleIn 150ms var(--ease-decelerate); }
```

---

## Accessibility

### Color Contrast (WCAG AA)
| Element | Ratio | Target |
|---------|-------|--------|
| Primary text on white | 12.6:1 | ✅ AAA |
| Secondary text on white | 4.5:1 | ✅ AA |
| Primary button text | 4.5:1 | ✅ AA |
| Link text | 4.5:1 | ✅ AA |

### Focus States
```css
*:focus-visible {
  outline: none;
  box-shadow: 0 0 0 4px var(--primary-light);
  border-radius: var(--radius-sm);
}

/* Skip link */
.skip-link {
  position: absolute;
  top: -100%;
  left: var(--space-4);
  padding: var(--space-2) var(--space-4);
  background: var(--primary);
  color: #FFFFFF;
  border-radius: var(--radius-md);
  z-index: 9999;
  transition: top 0.15s ease;
}

.skip-link:focus {
  top: var(--space-4);
}
```

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### Screen Reader Support
```html
<!-- Live region for status updates -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
  <!-- Dynamic status messages -->
</div>

<!-- Descriptive labels -->
<button aria-label="Close dialog" class="close-btn">×</button>
<input aria-describedby="hint-id" ... />
<p id="hint-id" class="input-hint">Helper text</p>
```

---

## Iconography

### System Icons (SF Symbols equivalents)
| Concept | Icon | Unicode |
|---------|------|---------|
| Search | 🔍 | U+1F50D |
| Analyze | 🔬 | U+1F52C |
| Settings | ⚙️ | U+2699 |
| History | 📜 | U+1F4DC |
| Download | 📥 | U+1F4E5 |
| Upload | 📤 | U+1F4E4 |
| Check | ✅ | U+2705 |
| Error | ❌ | U+274C |
| Warning | ⚠️ | U+26A0 |
| Info | ℹ️ | U+2139 |
| Expand | ▼ | U+25BC |
| Collapse | ▲ | U+25B2 |
| External Link | ↗️ | U+2197 |
| Copy | 📋 | U+1F4CB |
| Edit | ✏️ | U+270F |
| Delete | 🗑️ | U+1F5D1 |
| Add | ➕ | U+2795 |
| Filter | 🔽 | U+1F53D |

---

## Responsive Breakpoints

```css
/* Mobile First */
@media (min-width: 320px) { /* Base */ }
@media (min-width: 480px) { /* Small mobile */ }
@media (min-width: 768px) { /* Tablet */ }
@media (min-width: 1024px) { /* Desktop */ }
@media (min-width: 1440px) { /* Large desktop */ }
```

### Sidebar Behavior
| Breakpoint | Behavior |
|------------|----------|
| < 1024px | Collapsible drawer (hamburger menu) |
| ≥ 1024px | Persistent sidebar (320px) |

---

## Implementation Checklist

### Phase 1: Foundation ✅
- [x] Color system (light/dark)
- [x] Typography scale
- [x] Spacing system
- [x] CSS custom properties

### Phase 2: Core Components ✅
- [x] Button (primary, secondary, destructive)
- [x] Input field (with label, hint, error)
- [x] Card (base, metric, finding, phase)
- [x] Badge/pill (severity variants)
- [x] Sidebar section
- [x] Language selector

### Phase 3: Advanced Components
- [ ] Data table (sortable, filterable)
- [ ] Modal/dialog
- [ ] Toast/notification
- [ ] Progress indicator
- [ ] Skeleton loaders
- [ ] Tooltip/popover

### Phase 4: Polish
- [ ] Micro-interactions (hover, focus, active)
- [ ] Page transitions
- [ ] Loading states
- [ ] Empty states
- [ ] Error boundaries

---

## File Structure

```
app/
├── streamlit_app.py          # Main application
├── static/
│   ├── css/
│   │   ├── variables.css     # Design tokens
│   │   ├── reset.css         # Normalize
│   │   ├── components.css    # Component styles
│   │   ├── layout.css        # Grid, spacing
│   │   └── animations.css    # Motion
│   └── js/
│       └── interactions.js   # Progressive enhancement
└── templates/
    └── base.html             # Streamlit doesn't use templates
```

---

## Usage in Streamlit

```python
# Inject design system
st.markdown("""
<style>
  @import url('/static/css/variables.css');
  @import url('/static/css/components.css');
  @import url('/static/css/layout.css');
</style>
""", unsafe_allow_html=True)

# Use semantic class names
st.markdown('<div class="card finding-card finding-high">...</div>', unsafe_allow_html=True)
st.markdown('<button class="btn-primary">Analyze</button>', unsafe_allow_html=True)
st.markdown('<span class="badge badge-critical">Critical</span>', unsafe_allow_html=True)
```

---

*Design system v1.0 — Built for clarity, crafted for developers* 🍎