release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn tambox.wsgi --log-file -
