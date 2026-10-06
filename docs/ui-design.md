# UI Design System

## Palette

- **bg**: #0B1220
- **surface**: #111A2C
- **surface-2**: #16223A
- **border**: #22314D
- **text**: #E6EDF7
- **muted**: #8FA1BF
- **primary**: #3B82F6
- **success**: #22C55E
- **warning**: #F59E0B
- **danger**: #EF4444

## Severity Colors

Badge background at 15% opacity, text at full color:

- **critical**: #EF4444
- **high**: #F97316
- **medium**: #EAB308
- **low**: #22C55E
- **info**: #38BDF8

## Spacing Scale

4, 8, 12, 16, 24, 32 px

## Border Radius

- Cards: 10 px
- Badges and pills: 999 px

## Typography

- **Font stack**: Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif
- **No web fonts** (app must work offline)
- **Page title**: 28px / 700
- **Section title**: 18px / 600
- **Body**: 14px
- **Caption**: 12px muted
- **KPI numbers**: 32px / 700 with tabular numerals

## Rules

1. No emojis in the UI chrome (Windows does not render flag emojis)
2. Use Streamlit Material icons (`:material/icon_name:`) for buttons, tabs, and expanders
3. Never use color alone to carry meaning: severity badges always show their text
4. Contrast >= 4.5:1
5. Content max-width: 1200px, centered
6. Cards: surface background, 1px border, radius 10px, padding 16-20px
7. One primary button per screen area

## Layout

- **Content max-width**: 1200px, centered
- **Cards**: surface background, 1px border, radius 10px, padding 16-20px
- **One primary button per screen area**