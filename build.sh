#!/bin/bash
# Build script for Render deployment
set -e

echo "Installing Python dependencies..."
pip install "numpy==1.26.4"
pip install -r requirements.txt

echo "Installing Node.js dependencies..."
cd frontend
npm install

echo "Building frontend..."
npm run build
cd ..

echo "Build complete!"
