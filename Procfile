web: python3 manage.py migrate && python3 manage.py collectstatic --noinput && gunicorn game_collection.wsgi:application --bind 0.0.0.0:$PORT
