---
name: Aventura IA Playful Clean
colors:
  surface: '#fef7ff'
  surface-dim: '#e2d3ff'
  surface-bright: '#fef7ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f9f1ff'
  surface-container: '#f4eaff'
  surface-container-high: '#efe4ff'
  surface-container-highest: '#eaddff'
  on-surface: '#24005b'
  on-surface-variant: '#4a4455'
  inverse-surface: '#391e70'
  inverse-on-surface: '#f6edff'
  outline: '#7b7487'
  outline-variant: '#ccc3d8'
  surface-tint: '#732ee4'
  primary: '#630ed4'
  on-primary: '#ffffff'
  primary-container: '#7c3aed'
  on-primary-container: '#ede0ff'
  inverse-primary: '#d2bbff'
  secondary: '#6b38d4'
  on-secondary: '#ffffff'
  secondary-container: '#8455ef'
  on-secondary-container: '#fffbff'
  tertiary: '#005766'
  on-tertiary: '#ffffff'
  tertiary-container: '#007184'
  on-tertiary-container: '#b7efff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#eaddff'
  primary-fixed-dim: '#d2bbff'
  on-primary-fixed: '#25005a'
  on-primary-fixed-variant: '#5a00c6'
  secondary-fixed: '#e9ddff'
  secondary-fixed-dim: '#d0bcff'
  on-secondary-fixed: '#23005c'
  on-secondary-fixed-variant: '#5516be'
  tertiary-fixed: '#acedff'
  tertiary-fixed-dim: '#4cd7f6'
  on-tertiary-fixed: '#001f26'
  on-tertiary-fixed-variant: '#004e5c'
  background: '#fef7ff'
  on-background: '#24005b'
  surface-variant: '#eaddff'
  magic-sparkle: '#F59E0B'
  surface-lavender-subtle: '#F5F3FF'
  surface-lavender-soft: '#EDE9FE'
  success-mint: '#10B981'
typography:
  display-hero:
    fontFamily: Rubik
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-hero-mobile:
    fontFamily: Rubik
    fontSize: 36px
    fontWeight: '800'
    lineHeight: 44px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Rubik
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Rubik
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 34px
  headline-md:
    fontFamily: Rubik
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-sm:
    fontFamily: Rubik
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Nunito Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 28px
  body-md:
    fontFamily: Nunito Sans
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  label-lg:
    fontFamily: Rubik
    fontSize: 16px
    fontWeight: '700'
    lineHeight: 24px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Rubik
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  label-sm:
    fontFamily: Rubik
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.02em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  gutter: 1.25rem
  gutter-mobile: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.375rem
  space-sm: 0.75rem
  space-md: 1.25rem
  space-lg: 2rem
  space-xl: 3rem
---

## Brand & Style

This design system establishes a **Playful Clean & Tactile** aesthetic tailored for an interactive children's AI exploration showcase at a university fair. It balances childlike wonder, curiosity, and high technological clarity without descending into chaotic or overstimulating visual noise. 

The emotional target is magical, approachable, confident, and delightfully inviting. Complex artificial intelligence concepts are distilled into friendly, approachable tactile interactions. Interfaces utilize generous touch targets, luminous lavender-tinted surfaces, energetic purple gradients, and soft floating card elements that make interactions feel like pressing responsive physical buttons or magical tablets.

High-contrast readability and strict accessibility standards ensure children and attendees of all abilities can navigate, read, and interact comfortably across bright auditorium screens and mobile demonstration tablets.

## Colors

The palette revolves around a magical, luminous purple ecosystem anchored by deep, high-contrast structural text:

- **Primary (`#7C3AED` - Vivid Violet):** The dominant action color, driving key user journeys, principal CTA buttons, dynamic interactive badges, and energetic progress indicators.
- **Secondary (`#8B5CF6` - Bright Electric Purple):** Used for companion highlights, toggle states, playful badge surfaces, and gradient transitions paired with the primary violet.
- **Tertiary (`#06B6D4` - Cyber Cyan):** An electric technological accent signaling intelligence, discovery nodes, and interactive AI sparkles.
- **Neutral (`#2E1065` - Deep Cosmic Plum):** Replaces harsh standard blacks. Serves as the bedrock for typography, deep outlines, and accessible high-contrast graphic framing to maximize legibility.
- **Surfaces & Grounds (`#F5F3FF` & `#EDE9FE`):** Clean, airy, pastel-tinted backgrounds that eliminate glare while maintaining an inviting, non-sterile atmosphere.
- **Functional Accents (`#F59E0B` Sparkle Amber & `#10B981` Mint):** Instant reward indicators, quest achievements, and error-free confirmation cues.

## Typography

The typography leverages **Rubik** for all headlines and labels alongside **Nunito Sans** for body copy. Both typefaces feature rounded geometric contours, welcoming terminals, complete Latin extended character sets (with native support for Spanish tildes and "ñ"), and exceptional low-friction readability.

Headings carry heavy weights (Bold and Extra Bold) to convey enthusiasm and punchy visual anchors. Body text stays comfortably weighted at 500-600 in Nunito Sans to prevent wispy, low-contrast text strokes on bright screens or portable fair tablets. Line heights remain generous across all tiers to facilitate smooth reading for young audiences.

## Layout & Spacing

The layout utilizes a flexible 12-column responsive fluid grid on desktop and tablets (collapsing to a dedicated 4-column structure on mobile devices). The spatial framework maintains breathing room while preventing disjointed fragmentation:

- **Desktop & Large Displays:** Max-width container of `1200px`, centered with `2rem` outer page margins and `1.25rem` gutters.
- **Tablet / Fair Kiosks:** Full-width adaptive layout with `1.5rem` outer margins.
- **Mobile Handheld:** `1rem` outer margins and tight `0.75rem` gutters, prioritizing full-width tappable interactive card rows.

Interactive touch zones adhere to an expanded minimum threshold of `48px x 48px` (ideally `56px` height for primary actions) to support smaller motor control and casual exploratory taps.

## Elevation & Depth

Visual hierarchy uses a hybrid of **Tactile Extrusion** and **Luminous Ambient Shadows**:

- **Low Elevation (Resting Cards & Surfaces):** Pure white `#FFFFFF` or lavender `#F5F3FF` tiles sitting on top of light background planes, elevated with dual-tier soft purple drop shadows: `0 4px 12px -2px rgba(124, 58, 237, 0.08), 0 2px 6px -1px rgba(46, 16, 101, 0.04)`.
- **Medium Elevation (Buttons & Interactive Elements):** Deep tactile bevel effect created via subtle vertical offsets and bottom-border reinforcement (`box-shadow: 0 6px 0 0 #5B21B6`), giving controls a squishy, push-button feel.
- **High Elevation (Modals, Overlays, Floating Quest Badges):** Smooth ambient purple glow and drop shadow: `0 16px 32px -4px rgba(124, 58, 237, 0.18), 0 8px 16px -2px rgba(46, 16, 101, 0.08)`.
- **Gradients:** Subtle, directional magical gradients applied to key action cards and primary buttons (e.g., `linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)`).

## Shapes

The design system embraces an ultra-friendly, pill-influenced organic geometry (**Level 3** roundedness). 

Standard buttons, interactive tags, and inputs adopt full pill forms (`rounded-full` or `9999px`). Content cards, modals, and preview containers utilize substantial rounded corners (`rounded-2xl` / `1.5rem` to `rounded-3xl` / `2rem`), softening visual impact and eliminating sharp corners to reinforce the welcoming atmosphere.

## Components

### Buttons
- **Primary Action:** Pill-shaped (`rounded-full`), minimum height of `56px`, filled with vivid gradient `linear-gradient(135deg, #8B5CF6, #7C3AED)`, white bold Rubik text (`label-lg`), and an extruded tactile bottom edge (`box-shadow: 0 4px 0 0 #5B21B6`). On active press, the element shifts down by `3px` and reduces shadow depth.
- **Secondary Action:** Pill-shaped, soft lavender fill (`#EDE9FE`), text colored `#2E1065`, with a tactile border: `2px solid #DDD6FE`.
- **Icon / Magic Trigger:** Circular (`56px x 56px`), supporting large, crisp vector icons with subtle floating hover animations.

### Cards
- Built on `#FFFFFF` backgrounds with `rounded-3xl` (24px to 32px) corner radii.
- Border: `2px solid #EDE9FE` or borderless when paired with ambient purple elevation shadows.
- Inner padding follows `space-lg` (`2rem`) on desktop and `space-md` (`1.25rem`) on mobile.

### Chips & Badges
- Pill-shaped tags (`rounded-full`) with `space-xs` vertical and `space-md` horizontal padding.
- Light lavender background (`#F5F3FF`) paired with vivid purple text (`#7C3AED`) and a `1.5px` border in `#DDD6FE`.
- Achievement tags use amber sparkle (`#FEF3C7` background with `#B45309` text).

### Form Inputs
- Height `52px`, `rounded-full` or `rounded-2xl`, with `#FFFFFF` background and a distinct `2px solid #DDD6FE` resting border.
- Text in `#2E1065` with placeholder in `#8B5CF6` at 50% opacity.
- Focus state expands to a vibrant violet glow: `border-color: #7C3AED; box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.15)`.

### Checkboxes & Radios
- Oversized `28px x 28px` hit targets with soft corners (`rounded-lg` for checkboxes, `rounded-full` for radios).
- In checked state: solid `#7C3AED` background with a thick, playful white checkmark or center pip.

### Interactive AI Prompt & Activity Bubble
- Speech and AI prompt bubbles styled with `rounded-3xl` corners, a tiny organic tail, lavender wash (`#F5F3FF`), and glowing tertiary cyan borders (`#06B6D4`) denoting active AI assistance.