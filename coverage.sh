export PYTHONPATH=haruba
find . -name "*.pyc" -delete && py.test --cov-config .coveragerc --cov-report html --cov haruba
open htmlcov/index.html
