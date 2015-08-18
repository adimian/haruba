#!/bin/bash
export PYTHONPATH=haruba
virtualenv -p python3 .ve
source .ve/bin/activate
pip install -r requirements.txt
find . -name "*.pyc" -delete && py.test $@