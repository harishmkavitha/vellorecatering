# Responsive Media Check

Checked after GitHub deployment review.

## Fix applied
- Ensures `<picture>` inside `.page-hero__media` always fills the complete hero height.
- Keeps `object-fit: cover` for responsive cropping.
- Wedding hero now has dedicated desktop, tablet and mobile files.
- Reception hero already has dedicated desktop, tablet and mobile files.

## Breakpoints
- Mobile: up to 767px
- Tablet: 768px to 1199px
- Desktop/laptop: 1200px and above

## Quality rules
- Full-resolution local WebP images.
- No collage-extracted images for the current clean Wedding/Reception sets.
- No competitor catering names/logos/watermarks.
