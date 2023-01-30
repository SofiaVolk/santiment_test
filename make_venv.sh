#!/bin/sh
python3 -m venv ~/santiment_test/venv
source ~/santiment_test/venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r ~/santiment_test/requirements.txt