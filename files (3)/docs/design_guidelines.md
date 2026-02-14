# KNOUX OS Guardian - Design Guidelines

## 🎨 Visual Identity

### Brand Philosophy
KNOUX OS Guardian embodies **crystalline technology** - a fusion of transparency, precision, and advanced security. The design language communicates trustworthiness through glass morphism while maintaining a cutting-edge, high-tech aesthetic.

---

## Color System

### Primary Palette
- **Cyan (#00d9ff)**: Primary brand color, represents clarity and digital precision
- **Indigo (#6366f1)**: Secondary, adds depth and sophistication
- **Amber (#f59e0b)**: Accent color for warnings and calls-to-action

### Module-Specific Colors
Each module has a unique color identity:
```
Security:     #ef4444 (Red) - Protection, alerts
Backup:       #8b5cf6 (Purple) - Reliability, storage
Performance:  #10b981 (Green) - Optimization, health
Registry:     #f59e0b (Amber) - Maintenance, caution
Disk:         #06b6d4 (Cyan) - Space, organization
Network:      #3b82f6 (Blue) - Connectivity, flow
Driver:       #ec4899 (Pink) - Hardware, updates
Forensic:     #6366f1 (Indigo) - Analysis, investigation
Thermal:      #f97316 (Orange) - Heat, monitoring
Power:        #84cc16 (Lime) - Energy, efficiency
Apps:         #14b8a6 (Teal) - Applications, management
AI:           #a855f7 (Purple) - Intelligence, automation
```

---

## Typography

### Font Stack
```css
--font-display: 'Orbitron', 'Space Grotesk', sans-serif;
--font-body: 'Plus Jakarta Sans', 'Inter', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

### Usage Rules
- **Headings:** Orbitron (bold, uppercase for major headings)
- **Body Text:** Plus Jakarta Sans (regular, medium, semibold)
- **Data/Numbers:** Orbitron (for emphasis and tech feel)
- **Code/Technical:** JetBrains Mono

### Scale
```
5xl: 3rem     (48px) - Page titles
4xl: 2.25rem  (36px) - Module headers
3xl: 1.875rem (30px) - Section headings
2xl: 1.5rem   (24px) - Card titles
xl:  1.25rem  (20px) - Subheadings
lg:  1.125rem (18px) - Large body
base: 1rem    (16px) - Body text
sm:  0.875rem (14px) - Secondary text
xs:  0.75rem  (12px) - Labels, metadata
```

---

## Glass Morphism

### Core Principles
1. **Blur:** 12-32px backdrop blur for depth
2. **Saturation:** 180-200% for vibrancy
3. **Transparency:** 70-90% opacity
4. **Borders:** 1px semi-transparent highlights
5. **Shadows:** Layered for elevation

### Card Variants
```css
/* Standard Card */
backdrop-filter: blur(16px) saturate(180%);
background: rgba(19, 23, 34, 0.9);
border: 1px solid rgba(255, 255, 255, 0.1);

/* Elevated Card (Hover) */
backdrop-filter: blur(20px) saturate(200%);
transform: translateY(-8px);
box-shadow: 0 16px 64px rgba(0, 0, 0, 0.6);

/* Modal Overlay */
backdrop-filter: blur(32px) saturate(150%);
background: rgba(10, 14, 26, 0.9);
```

---

## Animation Principles

### Timing Functions
- **Fast:** 150ms - Micro-interactions (toggles, hovers)
- **Base:** 250ms - Standard transitions (cards, buttons)
- **Slow:** 350ms - Page transitions, modals
- **Bounce:** 500ms - Emphasis effects

### Stagger Delays
Progressive reveal with 100ms intervals:
```css
.stagger-1 { animation-delay: 0.1s; }
.stagger-2 { animation-delay: 0.2s; }
.stagger-3 { animation-delay: 0.3s; }
```

### Hover States
1. **Lift:** translateY(-8px)
2. **Scale:** 1.02-1.05x
3. **Glow:** 0 0 20px with color-specific glow
4. **Border:** Brighten from 0.3 to 1.0 opacity

---

## Spacing System

### Scale (rem-based)
```
xs:  0.25rem (4px)
sm:  0.5rem  (8px)
md:  1rem    (16px)
lg:  1.5rem  (24px)
xl:  2rem    (32px)
2xl: 3rem    (48px)
3xl: 4rem    (64px)
```

### Layout Rules
- **Grid Gap:** xl (32px) for module cards
- **Card Padding:** xl (32px) for content cards
- **Section Spacing:** 2xl-3xl (48-64px) between major sections
- **Component Spacing:** md-lg (16-24px) between related elements

---

## Border Radius

### Scale
```
sm:  0.375rem (6px)  - Small buttons, inputs
md:  0.5rem   (8px)  - Default components
lg:  0.75rem  (12px) - Cards, panels
xl:  1rem     (16px) - Large cards
2xl: 1.5rem   (24px) - Modals, overlays
full: 9999px         - Pills, badges, toggles
```

---

## Component Patterns

### Module Card
```
Structure:
- Icon (56x56px) with gradient background
- Title (font-display, text-xl)
- Description (font-body, text-sm)
- Stats (2-3 metrics with labels)
- Hover: lift + glow + border highlight
```

### Service Card
```
Structure:
- Header: Title + Status Badge
- Description (expandable)
- Metrics row (3 columns)
- Expandable details section
- Hover: left border accent
```

### Button Hierarchy
1. **Primary:** Gradient background, glow effect
2. **Secondary:** Glass background, border
3. **Ghost:** Transparent, border on hover
4. **Icon:** 44x44px minimum, glass background

---

## Responsive Breakpoints

```
Mobile:      < 480px  (1 column, compact)
Tablet:      768px    (2 columns, narrow sidebar)
Desktop:     1024px   (3 columns, full sidebar)
Large:       1920px   (4 columns, centered content)
```

### Mobile Adaptations
- Hide sidebar (hamburger menu)
- Remove search bar
- Stack footer elements
- Reduce font sizes by 10-15%
- Increase touch targets to 44px minimum

---

## Accessibility

### Contrast Ratios
- **Text:** Minimum 4.5:1 (AA)
- **Large Text:** Minimum 3:1 (AA)
- **Interactive Elements:** Minimum 3:1

### Focus Indicators
```css
:focus-visible {
  outline: 2px solid var(--knoux-primary);
  outline-offset: 2px;
}
```

### Motion Sensitivity
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Icon System

### Using Unicode Emoji
- **Pros:** Zero asset overhead, instant rendering
- **Cons:** Platform-dependent appearance
- **Recommendation:** Consistent across major platforms

### Icon Sizes
- **Small:** 16px (text-base)
- **Medium:** 24px (text-xl)
- **Large:** 32px (text-2xl)
- **XL:** 48px (text-3xl)
- **Module Icon:** 56px

---

## Shadow System

### Elevation Layers
```css
sm:  0 2px 8px rgba(0, 0, 0, 0.3)   - Subtle depth
md:  0 4px 16px rgba(0, 0, 0, 0.4)  - Cards
lg:  0 8px 32px rgba(0, 0, 0, 0.5)  - Elevated cards
xl:  0 16px 64px rgba(0, 0, 0, 0.6) - Modals
```

### Colored Glows
```css
primary: 0 0 20px rgba(0, 217, 255, 0.5)
secondary: 0 0 20px rgba(99, 102, 241, 0.4)
accent: 0 0 20px rgba(245, 158, 11, 0.4)
```

---

## Best Practices

### DO ✓
- Use glass morphism for primary UI surfaces
- Apply consistent spacing from design tokens
- Stagger animations for visual hierarchy
- Maintain 4.5:1 contrast ratios
- Use semantic HTML elements
- Test on mobile devices

### DON'T ✗
- Overuse animations (keep under 3 per view)
- Mix multiple font families
- Use solid backgrounds (breaks glass aesthetic)
- Ignore reduced motion preferences
- Create deeply nested glass layers (max 3)
- Use absolute positioning excessively

---

## Performance Guidelines

### Animation Performance
- Prefer `transform` and `opacity` (GPU-accelerated)
- Avoid animating `width`, `height`, `top`, `left`
- Use `will-change` sparingly
- Cap animations at 60fps

### CSS Optimization
- Use CSS custom properties for theming
- Minimize specificity (class-based selectors)
- Avoid `@import` (use `<link>` tags)
- Group media queries at end of file

---

## Future Enhancements

### Planned Additions
- Dark/Light theme auto-switching based on time
- Custom color picker for personalization
- Additional animation presets
- More module-specific visual treatments
- Enhanced data visualization components

---

**Design Version:** 1.0.0  
**Last Updated:** February 2025  
**Design System:** Crystalline Glass Morphism
