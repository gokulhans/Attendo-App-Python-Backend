#!/bin/bash

# Check if running in production mode
if [ "$FLASK_ENV" = "production" ]; then
    echo "Starting production server with Gunicorn..."
    gunicorn wsgi:app
else
    echo "Starting development server..."
    python main.py
fi 