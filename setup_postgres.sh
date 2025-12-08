#!/bin/bash
# Quick PostgreSQL setup script for PaperBot

echo "Setting up PostgreSQL database for PaperBot..."

# Try to create database (adjust password as needed)
PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE paperbot;" 2>/dev/null || echo "Database may already exist"

# Or if no password, try:
# sudo -u postgres psql -c "CREATE DATABASE paperbot;"
# sudo -u postgres psql -c "CREATE USER paperbot_user WITH PASSWORD 'paperbot_pass';"
# sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE paperbot TO paperbot_user;"

echo "✅ Database setup complete!"
echo ""
echo "Update your .env file with:"
echo "USE_SQLITE=False"
echo "DB_NAME=paperbot"
echo "DB_USER=postgres"
echo "DB_PASSWORD=your_password"
echo "DB_HOST=localhost"
echo "DB_PORT=5432"



