# Despliegue en VPS de Hostinger (Ubuntu 24.04)

Guía paso a paso para poner MAS tour en producción con **gunicorn + nginx + systemd + SSL**.
Stack en el servidor: Python 3.12 · uv · SQLite · nginx.

## 0. Preparativos (antes de tocar el VPS)

1. En hPanel de Hostinger crea el VPS eligiendo la plantilla **Ubuntu 24.04 LTS** (sin panel).
   Anota la **IP pública** (hPanel → VPS → Información).
2. Apunta tu dominio al VPS: en la zona DNS crea un registro **A** `@` → IP del VPS y otro
   **A** `www` → IP del VPS. (Si el dominio está en Hostinger: hPanel → Dominios → DNS.)
3. Sube el código a un repositorio Git (GitHub/GitLab privado). Alternativa sin Git: `rsync`.
   > Importante: `db.sqlite3` y `media/` contienen tus datos locales de prueba; decide si los
   > llevarás al servidor (paso 10) o empezarás con datos limpios.

## 1. Conectarse al VPS

```bash
ssh root@TU_IP        # contraseña o clave SSH definida al crear el VPS en hPanel
```

## 2. Actualizar el sistema y crear un usuario de despliegue

```bash
apt update && apt upgrade -y
adduser deploy                 # elige una contraseña
usermod -aG sudo deploy
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
su - deploy
```

## 3. Instalar software base

```bash
sudo apt install -y nginx git
curl -LsSf https://astral.sh/uv/install.sh | sh    # instala uv
source ~/.bashrc                                    # (o vuelve a entrar) para tener `uv` en PATH
```

## 4. Clonar el proyecto e instalar dependencias

```bash
cd ~
git clone https://github.com/TU_USUARIO/Excursiones.git excursiones
cd excursiones
uv sync                # crea .venv con Django, Pillow, PydanticAI, etc.
uv add gunicorn        # servidor WSGI de producción
```

## 5. Variables de entorno de producción

Genera una SECRET_KEY nueva:

```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Crea el archivo `/home/deploy/excursiones/.env.prod`:

```bash
nano /home/deploy/excursiones/.env.prod
```

```ini
DJANGO_SECRET_KEY=PEGA_AQUI_LA_CLAVE_GENERADA
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tudominio.com,www.tudominio.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://tudominio.com,https://www.tudominio.com
GEMINI_API_KEY=TU_API_KEY_DE_GOOGLE_AI_STUDIO
```

Protégelo: `chmod 600 .env.prod`

> Sin dominio todavía: usa `DJANGO_ALLOWED_HOSTS=TU_IP` y omite el paso 9 (SSL).

## 6. Preparar la aplicación

```bash
cd ~/excursiones
set -a; source .env.prod; set +a          # carga las variables en esta sesión
uv run python manage.py migrate           # crea la BD (incluye localidades/categorías semilla)
uv run python manage.py createsuperuser   # admin real (NO uses admin/admin12345)
uv run python manage.py collectstatic --noinput   # copia estáticos a staticfiles/
```

Prueba rápida de que gunicorn arranca (Ctrl+C para salir):

```bash
uv run gunicorn config.wsgi:application --bind 127.0.0.1:8001
```

## 7. Servicio systemd (arranque automático)

```bash
sudo nano /etc/systemd/system/excursiones.service
```

```ini
[Unit]
Description=MAS tour (gunicorn)
After=network.target

[Service]
User=deploy
Group=www-data
WorkingDirectory=/home/deploy/excursiones
EnvironmentFile=/home/deploy/excursiones/.env.prod
ExecStart=/home/deploy/excursiones/.venv/bin/gunicorn config.wsgi:application \
    --workers 3 --bind unix:/home/deploy/excursiones/gunicorn.sock
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now excursiones
sudo systemctl status excursiones        # debe decir "active (running)"
```

## 8. Nginx (proxy inverso + estáticos + media)

```bash
sudo nano /etc/nginx/sites-available/excursiones
```

```nginx
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;

    client_max_body_size 100M;   # subida de fotos y videos desde el admin

    location /static/ {
        alias /home/deploy/excursiones/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /home/deploy/excursiones/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://unix:/home/deploy/excursiones/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/excursiones /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
# nginx necesita poder atravesar /home/deploy:
sudo chmod o+x /home/deploy
```

En este punto la web ya responde en `http://tudominio.com`.

## 9. SSL gratis con Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tudominio.com -d www.tudominio.com
```

Certbot configura HTTPS y la renovación automática. Verifica: `https://tudominio.com`.

## 10. (Opcional) Llevar tus datos locales al servidor

Desde tu PC (PowerShell, con OpenSSH):

```powershell
scp C:\Users\lilia\Desktop\Projects\Personal\Excursiones\db.sqlite3 deploy@TU_IP:/home/deploy/excursiones/
scp -r C:\Users\lilia\Desktop\Projects\Personal\Excursiones\media deploy@TU_IP:/home/deploy/excursiones/
```

Luego en el VPS: `sudo systemctl restart excursiones`.
(Si prefieres datos limpios, simplemente carga todo desde `/admin/`.)

## 11. Actualizar la app tras cambios

```bash
cd ~/excursiones
git pull
uv sync
set -a; source .env.prod; set +a
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
sudo systemctl restart excursiones
```

## 12. Copias de seguridad (recomendado)

```bash
crontab -e
# todos los días a las 3:00 AM, conserva 14 días:
0 3 * * * cd /home/deploy/excursiones && tar czf ~/backups/excursiones-$(date +\%F).tar.gz db.sqlite3 media && find ~/backups -mtime +14 -delete
```

(Crea antes la carpeta: `mkdir -p ~/backups`.)

## Solución de problemas

| Síntoma | Revisar |
|---|---|
| 502 Bad Gateway | `sudo journalctl -u excursiones -n 50` (gunicorn caído o socket sin permisos) |
| Estáticos sin estilo | ¿Ejecutaste `collectstatic`? ¿El `alias` de nginx apunta a `staticfiles/`? |
| 400 Bad Request | `DJANGO_ALLOWED_HOSTS` no incluye el dominio exacto |
| Error CSRF al reservar | `DJANGO_CSRF_TRUSTED_ORIGINS` debe llevar `https://` delante |
| El chatbot no responde | Falta `GEMINI_API_KEY` en `.env.prod` |
| No suben fotos grandes | Aumenta `client_max_body_size` en nginx |
