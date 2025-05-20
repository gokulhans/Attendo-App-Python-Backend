#!/usr/bin/env bash
# exit on error
set -o errexit

# Set environment variables for dlib
export DLIB_USE_CUDA=0
export FORCE_CMAKE=1

# Install Python packages
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Create necessary directories
mkdir -p ~/.cache/dlib

# Install system dependencies
apt-get update
apt-get install -y build-essential cmake
apt-get install -y libopenblas-dev liblapack-dev
apt-get install -y libx11-dev libgtk-3-dev
apt-get install -y python3-dev

# Install Python packages
pip install -r requirements.txt 