# Tailwind CSS Build Files

This folder contains the Tailwind CSS build configuration and source files. Since the production CSS is already built and available at `presentation/web/static/css/tailwind.css`, you typically don't need to rebuild unless you're making styling changes.

## Files:
- `package.json` - Node.js dependencies for Tailwind
- `tailwind.config.js` - Tailwind configuration
- `input.css` - Source CSS with Tailwind directives
- `build-css.sh` - Build script for regenerating CSS

## When to Rebuild:
- Adding new Tailwind classes to HTML templates
- Modifying the Tailwind configuration
- Updating custom CSS components in `input.css`

## Quick Rebuild:
```bash
cd tailwind/
npm install
./build-css.sh
```

This will regenerate `../presentation/web/static/css/tailwind.css` with your changes.