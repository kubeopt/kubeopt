#!/bin/bash

# Build CSS for production deployment
echo "🎨 Building Tailwind CSS for production..."

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build production CSS
echo "🔨 Building production CSS..."
npm run build-css-prod

# Check if the build was successful
if [ -f "../presentation/web/static/css/tailwind.css" ]; then
    echo "✅ Tailwind CSS build successful!"
    echo "📁 Output: ../presentation/web/static/css/tailwind.css"
    
    # Show file size
    size=$(du -h ../presentation/web/static/css/tailwind.css | cut -f1)
    echo "📊 File size: $size"
else
    echo "❌ Build failed! CSS file not generated."
    exit 1
fi

echo "🎉 CSS build complete!"