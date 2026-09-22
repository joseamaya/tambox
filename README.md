# tambox

Software de Logística: requerimientos, compras, almacén, contabilidad, productos
y administración, sobre Django 5.2 y PostgreSQL.

## Requisitos

- Python 3.12 (ver `.python-version`)
- PostgreSQL

## Poner el entorno en marcha

1. Entorno virtual y dependencias:

   ```bash
   python3.12 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

2. Configuración: copia `.env.example` a `.env` y completa los valores.

   En desarrollo el archivo es opcional: `tambox.settings.development` usa por
   defecto la base `tambox`, con usuario `tambox`, en `localhost:5432`, y trae
   una `SECRET_KEY` de desarrollo.

3. Crea las tablas:

   ```bash
   .venv/bin/python manage.py migrate
   ```

4. Crea el primer usuario, que es con el que se entra:

   ```bash
   .venv/bin/python manage.py createsuperuser
   ```

5. Levanta el servidor y abre http://localhost:8000/ :

   ```bash
   .venv/bin/python manage.py runserver
   ```

## Datos mínimos

La aplicación necesita unos datos básicos: la oficina GERENCIA GENERAL, los
niveles de aprobación LOGISTICA y USUARIO, el tipo de documento PEC, los tipos
de movimiento I00 / I01 / S01 y la unidad de medida SERV. Sin el nivel USUARIO,
por ejemplo, no se puede registrar un requerimiento.

No hay que cargarlos a mano: **entra una vez a los tableros de Administración,
Contabilidad y Almacén** y se crean solos. Son idempotentes, así que si falta
solo uno se completa ese y no se duplica el resto.

## Pruebas y verificación

```bash
.venv/bin/python manage.py test      # tests
.venv/bin/ruff check .               # lint
.venv/bin/python manage.py check     # chequeos de Django
```

Es lo mismo que corre `.github/workflows/ci.yml` en cada push.

## Configuración por entorno

Todo se lee de variables de entorno, o del `.env` en desarrollo. Las de
producción están comentadas en `.env.example`: `DATABASE_URL`, `ALLOWED_HOSTS`,
`CSRF_TRUSTED_ORIGINS`, `LOG_LEVEL`, `SECURE_SSL_REDIRECT` y
`SECURE_HSTS_SECONDS`.

En producción se arranca con `gunicorn` (ver `Procfile`) y
`tambox.settings.production`, donde `DEBUG` es `False` y no hay valores por
defecto para la clave secreta ni para la base.

## Despliegue

El `Procfile` trae dos procesos:

- `release`: `migrate` y `collectstatic --noinput`. Es obligatorio: sin
  `collectstatic` no existe el manifest y los `{% static %}` de las plantillas
  fallan (la página de login da error).
- `web`: `gunicorn tambox.wsgi`.

El sitio se asume detrás de un proxy que termina el TLS: `production` fuerza
`SECURE_SSL_REDIRECT` y las cookies seguras, y lee `X-Forwarded-Proto`. HSTS se
activa solo si defines `SECURE_HSTS_SECONDS` (por defecto `0`), porque es difícil
de revertir.

Los archivos subidos (`MEDIA_ROOT`: logos, imágenes de productos, firmas) **no**
los sirve `whitenoise`, que solo atiende los estáticos. Hay que servirlos con el
proxy inverso en `/media/` o con un almacenamiento de objetos.

Antes de desplegar conviene pasar:

```bash
DJANGO_SETTINGS_MODULE=tambox.settings.production \
  .venv/bin/python manage.py check --deploy
```
