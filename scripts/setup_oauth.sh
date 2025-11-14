#!/bin/bash

# Setup script for Google OAuth authentication
# This script helps configure the OAuth system for the Dividend API

set -e

echo "======================================"
echo "Google OAuth Setup for Dividend API"
echo "======================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "Generating secure secrets..."

# Generate SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
SESSION_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Update .env file
if grep -q "SECRET_KEY=your-secret-key" .env; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
        sed -i '' "s|SESSION_SECRET=.*|SESSION_SECRET=$SESSION_SECRET|" .env
    else
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
        sed -i "s|SESSION_SECRET=.*|SESSION_SECRET=$SESSION_SECRET|" .env
    fi
    echo "✓ Generated and saved SECRET_KEY"
    echo "✓ Generated and saved SESSION_SECRET"
else
    echo "✓ Secrets already configured"
fi

echo ""
echo "Installing Python dependencies..."
pip install authlib python-jose[cryptography] itsdangerous --quiet
echo "✓ OAuth dependencies installed"

echo ""
echo "Setting up database..."

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "⚠ Warning: psql command not found. Skipping database setup."
    echo "  Please run manually: psql -d dividend_db -f migrations/create_users_table.sql"
else
    # Try to connect to database
    if psql -d dividend_db -c "SELECT 1" &> /dev/null; then
        echo "Running database migration..."
        psql -d dividend_db -f migrations/create_users_table.sql
        echo "✓ Database migration completed"
    else
        echo "⚠ Warning: Could not connect to dividend_db database"
        echo "  Please run manually: psql -d dividend_db -f migrations/create_users_table.sql"
    fi
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Set up Google OAuth credentials:"
echo "   - Go to https://console.cloud.google.com/"
echo "   - Create OAuth 2.0 credentials"
echo "   - Add redirect URI: http://localhost:8000/auth/callback"
echo ""
echo "2. Update .env file with your Google OAuth credentials:"
echo "   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com"
echo "   GOOGLE_CLIENT_SECRET=your-client-secret"
echo ""
echo "3. Start the application:"
echo "   uvicorn api.main:app --reload"
echo ""
echo "4. Visit the login page:"
echo "   http://localhost:8000/login"
echo ""
echo "For detailed instructions, see: docs/GOOGLE_OAUTH_SETUP.md"
echo ""
