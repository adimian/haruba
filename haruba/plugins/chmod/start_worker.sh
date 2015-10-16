#!/bin/bash
export CHMOD_AMQP_USER=guest
export CHMOD_AMQP_PASSWORD=guest
export CHMOD_AMQP_HOST=192.168.111.193
export PYTHONPATH=PYTHONPATH:..

python3 worker.py