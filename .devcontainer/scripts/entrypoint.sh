#!/bin/bash
set -e

# waitfor the database
sleep 5

# execute db migration
flask db migrate || echo "No changes to migrate"
flask db upgrade

# start Flask
exec flask run --host=0.0.0.0 --port=5000
