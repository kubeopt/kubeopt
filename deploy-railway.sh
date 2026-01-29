#!/bin/bash

# KubeOpt Railway Deployment Script
# This script prepares and validates the Railway deployment setup

echo "🚂 KubeOpt Railway Deployment Preparation"
echo "========================================"

# Check if required files exist
echo "📋 Checking deployment files..."

REQUIRED_FILES=(
    "railway.toml"
    "Dockerfile.railway" 
    "wsgi.py"
    "requirements/requirements.txt"
    "RAILWAY-DEPLOYMENT.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file - Found"
    else
        echo "❌ $file - Missing"
        exit 1
    fi
done

# Check if environment variables are set in .env file
echo ""
echo "📋 Checking environment configuration..."

if [ -f ".env" ]; then
    echo "✅ .env file found"
    
    # Check for required Azure variables
    if grep -q "AZURE_CLIENT_ID=" .env && grep -q "AZURE_CLIENT_SECRET=" .env; then
        echo "✅ Azure credentials configured"
    else
        echo "⚠️  Azure credentials need to be configured in .env file"
    fi
else
    echo "❌ .env file not found"
    echo "Please copy .env.example to .env and configure your settings"
    exit 1
fi

# Check if gunicorn is in requirements
echo ""
echo "📋 Checking dependencies..."

if grep -q "gunicorn" requirements/requirements.txt; then
    echo "✅ Gunicorn dependency found"
else
    echo "❌ Gunicorn not found in requirements.txt"
    exit 1
fi

echo ""
echo "🎉 Railway deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Push your code to GitHub repository"
echo "2. Create new Railway project from GitHub repo"
echo "3. Configure environment variables in Railway dashboard"
echo "4. Deploy and access your KubeOpt instance"
echo ""
echo "📚 See RAILWAY-DEPLOYMENT.md for detailed instructions"