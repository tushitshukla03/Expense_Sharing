#!/bin/bash

# Create virtual environment
python3 -m venv .env

# Activate virtual environment
exec ".env/bin/python" build.py
