---
name: LensCloud Service Portal
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#434655'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#747686'
  outline-variant: '#c4c5d7'
  surface-tint: '#2151da'
  primary: '#0037b0'
  on-primary: '#ffffff'
  primary-container: '#1d4ed8'
  on-primary-container: '#cad3ff'
  inverse-primary: '#b7c4ff'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fb'
  on-secondary-container: '#54647a'
  tertiary: '#7f2500'
  on-tertiary: '#ffffff'
  tertiary-container: '#a73400'
  on-tertiary-container: '#ffc9b7'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dce1ff'
  primary-fixed-dim: '#b7c4ff'
  on-primary-fixed: '#001551'
  on-primary-fixed-variant: '#0039b5'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#ffdbcf'
  tertiary-fixed-dim: '#ffb59c'
  on-tertiary-fixed: '#390c00'
  on-tertiary-fixed-variant: '#832700'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
  frappe-blue: '#1D4ED8'
  slate-gray: '#64748B'
  emerald-green: '#10B981'
  border-subtle: '#EDEDED'
  text-muted: '#7C7C7C'
typography:
  display:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 32px
---

## Brand & Style

The design system is engineered for high-utility SaaS environments, prioritizing clarity, efficiency, and professional trust. It adopts a **Corporate / Modern** aesthetic, heavily influenced by the Frappe ecosystem's focus on structured data and clean "workspace" metaphors. 

The personality is helpful yet unobtrusive, functioning as a silent facilitator for complex workflows. The UI utilizes ample whitespace, refined border-based containment, and a strict typographic hierarchy to ensure that users can navigate dense customer data and onboarding flows without cognitive fatigue. The style emphasizes functional elegance over decorative flair, ensuring long-term usability for professional operators.

## Colors

The palette is anchored by **Frappe Blue** (#1D4ED8), used exclusively for primary actions, progress indicators, and active states. **Slate Gray** functions as the structural backbone, providing a range of tones for borders, secondary iconography, and auxiliary text. 

A high-contrast neutral foundation uses pure white surfaces against a very light gray background (#F8FAFC) to create subtle layering. **Emerald Green** is reserved strictly for success messaging and "Completed" statuses within onboarding flows. This restrained approach ensures that color always signals meaning, never just decoration.

## Typography

The system utilizes **Inter** for its exceptional legibility in data-heavy interfaces. The typographic scale is compact, favoring 14px for standard body text to maximize information density. 

Headlines use a tighter letter-spacing to appear more authoritative and modern. Labels and captions use a slightly reduced font size with increased weight to distinguish them from editable data. For mobile views, large display headings are scaled down to ensure clear visibility without excessive scrolling.

## Layout & Spacing

This design system uses a **Fixed Grid** approach for desktop views to maintain focus, centered within a maximum container width of 1280px. The layout follows a 12-column structure with 24px gutters.

Spacing is based on a 4px baseline grid. Internal component padding follows a strict logic: 8px for small elements, 16px for standard card interiors, and 24px–32px for section separation. On mobile devices, the grid collapses to a single column with 16px horizontal margins. Horizontal scrolling is permitted only for data tables; all other content must reflow vertically.

## Elevation & Depth

The design system employs **low-contrast outlines** rather than heavy shadows to define depth. This reflects the Frappe UI philosophy of "flat but layered." 

1. **Level 0 (Background):** The base layer uses a soft neutral tint.
2. **Level 1 (Cards/Surfaces):** Primary content containers use white backgrounds with a 1px border (#EDEDED). No shadow is used in its resting state.
3. **Level 2 (Dropdowns/Modals):** Elements that sit above the primary plane use a very subtle, diffused shadow (0px 4px 12px rgba(0,0,0,0.05)) combined with a 1px border to ensure separation from the content below.

## Shapes

The shape language is **Soft**, utilizing a standard 0.25rem (4px) corner radius for buttons, inputs, and small containers. This creates a precision-oriented look that feels approachable but disciplined. 

Larger containers like cards or onboarding modals may use up to 8px (rounded-lg) to soften the overall layout. Avatars and status "pips" are the only exception, utilizing fully circular (pill) shapes to distinguish them from structural UI elements.

## Components

### Buttons & Inputs
Buttons feature a solid fill for primary actions (Frappe Blue) and a ghost-style (slate-gray border) for secondary actions. Input fields use a 1px #EDEDED border that transitions to #1D4ED8 on focus.

### Guided Onboarding
Onboarding steps are visualized through a "Vertical Stepper" component in sidebars or a "Progress Bar" at the top of cards. Completed steps utilize the Emerald Green checkmark.

### Cards & Lists
Cards are restrained, using 1px borders instead of shadows. Data lists within cards should have 1px horizontal dividers and use `body-sm` typography to maintain a compact, professional feel.

### Chips & Badges
Use for status indicators (e.g., "Active," "Pending," "Success"). Badges use a desaturated background of the status color with high-contrast text for maximum readability.

### Empty States
Guided onboarding flows should include "Blank Slates" that use a centered illustration, a clear `headline-md` title, and a single primary action button to direct the user's next move.