# Tailwind CSS Production Build Guide

This project has been updated to use a production-ready Tailwind CSS setup instead of the CDN version.

## Quick Start

### Prerequisites
- Node.js 16+ and npm
- Python 3.11+

### Development Setup

1. **Install CSS dependencies:**
   ```bash
   npm install
   ```

2. **Build CSS for development (with watch mode):**
   ```bash
   npm run dev
   ```

3. **Build CSS for production:**
   ```bash
   npm run prod
   ```

   Or use the build script:
   ```bash
   ./build-css.sh
   ```

## File Structure

```
├── package.json              # Node.js dependencies and scripts
├── tailwind.config.js        # Tailwind configuration
├── build-css.sh             # Build script for production
├── presentation/web/static/css/
│   ├── input.css            # Source CSS with Tailwind directives
│   └── tailwind.css         # Generated production CSS
└── presentation/web/templates/
    └── *.html               # HTML templates using Tailwind classes
```

## Configuration

### Tailwind Config (`tailwind.config.js`)
- **Content paths**: Scans HTML templates, JS files, and Python files for classes
- **Custom theme**: Extended with primary colors and Inter font
- **Plugins**: Ready for additional Tailwind plugins

### Build Scripts (`package.json`)
- `npm run dev`: Development build with watch mode
- `npm run prod`: Production build with minification

## Production Deployment

### Docker
Use the provided `Dockerfile.simple` for containerized deployments:

```bash
docker build -f Dockerfile.simple -t aks-cost-optimizer .
docker run -p 8000:8000 aks-cost-optimizer
```

### Manual Deployment
1. Install Node.js dependencies: `npm install`
2. Build production CSS: `npm run prod`
3. Deploy the application with the generated `tailwind.css`

## Benefits of This Setup

✅ **Performance**: Minified CSS bundle (~10KB vs ~3MB CDN)
✅ **Reliability**: No external CDN dependencies
✅ **Customization**: Full control over Tailwind configuration
✅ **Security**: No external script loading
✅ **Offline Support**: Works without internet connection

## Custom Styles

The `input.css` file includes custom component classes:
- `.btn-primary`, `.btn-secondary` - Button styles
- `.card`, `.dashboard-metric` - Layout components  
- `.alert-*` - Alert/notification styles

## Troubleshooting

### CSS Not Building
```bash
# Check Node.js version
node --version  # Should be 16+

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Manual build
npx tailwindcss -i ./presentation/web/static/css/input.css -o ./presentation/web/static/css/tailwind.css --minify
```

### Missing Styles
Ensure your HTML content is included in `tailwind.config.js` content paths:
```javascript
content: [
  "./presentation/web/templates/**/*.html",
  "./presentation/web/static/js/**/*.js",
  "./infrastructure/services/**/*.py"
]
```

## Development Workflow

1. Start CSS watch mode: `npm run dev`
2. Edit HTML templates using Tailwind classes
3. CSS automatically rebuilds when files change
4. For production: `npm run prod` before deployment