#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install dependencies
pip install -r requirements.txt

# 2. Convert static assets
python manage.py collectstatic --no-input

# 3. Apply database migrations (Fixes "UndefinedTable" error)
python manage.py migrate

# 4. Auto-Create Superuser (Only if it doesn't exist)

python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('emmanuel', 'onene244@gmail.com', '1029384756')"
