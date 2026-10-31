#!/usr/bin/env bash
set -o errexit

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python backend/manage.py collectstatic --noinput

echo "Applying database migrations..."
python backend/manage.py migrate

echo "Build completed successfully!"
