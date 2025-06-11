#!/bin/bash
# setup.sh

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "Environment setup complete. To activate: source venv/bin/activate"
