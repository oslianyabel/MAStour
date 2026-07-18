# Excursiones

Aplicación web Django para gestionar excursiones turísticas con reservas en línea y
confirmación vía WhatsApp.

## Casos de uso
- **Administradores**: gestionan dinámicamente excursiones, salidas (slots), guías, ofertas
  gastronómicas, puntos de recogida, categorías, localidades y reservas desde el panel de
  administración de Django (`/admin/`).
- **Clientes**: navegan las excursiones disponibles para los próximos días, filtran por
  categoría y destino, ven fotos/videos/mapa, y reservan plazas. Al completar la reserva son
  redirigidos al chat de WhatsApp del organizador con los datos de la reserva.
- **Clientes (chatbot)**: conversan con el asistente virtual (botón flotante presente en todo
  el sitio) para consultar excursiones, precios, disponibilidad de salidas, reservas por
  teléfono y canales de contacto.

## Tecnologías
- Python 3.12 · Django 6 · SQLite (desarrollo)
- Pillow (imágenes) · Leaflet + OpenStreetMap (mapas)
- PydanticAI + Google Gemini (chatbot con tools sobre la BD)
- CSS propio, responsive y mobile-first (sin frameworks)
- uv (gestión de dependencias) · ruff (linting)

## Características notables
- Validación de capacidad con bloqueo de fila (`select_for_update`) que evita sobreventa
  incluso con reservas concurrentes.
- Redirección automática a `wa.me` con el mensaje de la reserva prellenado.
- Punto de recogida "por definir" hasta que la salida agota su capacidad; el admin resalta
  las salidas agotadas que necesitan punto de recogida.
- Datos semilla de localidades y categorías vía migración.
- Página "Sobre Nosotros" y página 404 personalizada (previsualizable en `/404-preview/` en DEBUG).
- Redes sociales (Instagram, Facebook, WhatsApp, YouTube, X) gestionables desde el admin y
  mostradas en el footer; el enlace de WhatsApp alimenta el CTA de contacto de "Sobre Nosotros".
- Equipo de "Sobre Nosotros" (nombre, cargo, frase, foto, orden) editable desde el admin.
- Estado de salidas Pendiente/Completada con transición automática al vencer la hora de
  retorno (zona horaria de La Habana); las completadas dejan de ser reservables.
- "Recuerdos": álbumes de imágenes por salida completada (admin) mostrados en la página
  "Excursiones realizadas", con lightbox para ampliar cada imagen.
- Preguntas frecuentes gestionables desde el admin (pregunta, respuesta, orden, activa) y
  publicadas en `/preguntas-frecuentes/` como acordeón.
- Chatbot flotante (diseño Figma responsive) con agente PydanticAI: herramientas de solo
  lectura sobre toda la BD (excursiones, salidas, disponibilidad, guías, ofertas, reservas,
  redes sociales), historial persistido por sesión en la tabla `chatbot_chatmessage` y
  respuestas con enlaces navegables a detalles/reserva.
- Prompt del sistema del chatbot editable desde el admin (modelo `ChatbotPrompt`, sembrado
  desde `prompt.txt`); el agente se reconstruye automáticamente al guardar cambios, sin
  reiniciar el servidor.
- Panel de administración con tema personalizado de la marca: logo y tipografía Inter,
  paleta del sitio (verde oliva `#4a5d23`, naranja `#f47920`), tarjetas y botones
  redondeados, soporte de modo claro/oscuro (`templates/admin/base_site.html` +
  `static/css/admin.css`).

## Arquitectura
```
config/            Configuración del proyecto Django (settings, urls)
tours/             App principal
├── models.py      Entidades: Category, Location, Guide, GastronomicOffer, Excursion,
│                  OptionalActivity, ExcursionPhoto, ExcursionVideo, PickupPoint, Slot,
│                  Reservation, SocialLink, TeamMember, Memory, MemoryImage, Faq
├── services.py    Lógica de negocio: creación de reservas con bloqueo, URL de WhatsApp
├── forms.py       Formulario de reserva con validación de capacidad
├── views.py       Listado, detalle y reserva
└── admin.py       Panel de administración con inlines e indicadores de disponibilidad
chatbot/           App del asistente virtual
├── ai_agent/      Agente PydanticAI: agent.py, tools.py (consultas BD), chat_history.py,
│                  prompt.txt (prompt semilla/fallback)
├── models.py      ChatMessage (historial por sesión), ChatbotPrompt (prompt editable)
├── views.py       Endpoint JSON GET/POST /chatbot/mensajes/
└── urls.py        Rutas del chatbot
templates/         Plantillas (base + tours, incluye widget del chatbot)
static/css/        Estilos mobile-first
scripts/           Scripts de verificación manual (datos demo)
context/specs/     Reglas de negocio
media/             Archivos subidos (fotos, videos)
```

## Base de datos
SQLite (`db.sqlite3`) en desarrollo. Para producción se recomienda PostgreSQL.

## Variables de entorno
- `GEMINI_API_KEY` (requerida para el chatbot): API key de Google AI Studio. Sin ella, el
  chatbot responde con un mensaje de contingencia.
Para producción: configurar además `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS` y la base
de datos.

## APIs / servicios externos
- **WhatsApp (wa.me)**: enlaces de chat con mensaje prellenado (no requiere API key).
- **OpenStreetMap / Leaflet (CDN)**: mapas del destino (no requiere API key).
- **Google Gemini (via PydanticAI)**: modelo `gemini-flash-latest` para el chatbot
  (requiere `GEMINI_API_KEY`).

## Cómo ejecutar
```bash
uv sync                                   # instalar dependencias
uv run python manage.py migrate           # aplicar migraciones (incluye datos semilla)
uv run python manage.py createsuperuser   # crear admin
uv run python scripts/seed_demo_data.py   # (opcional) datos de demostración
uv run python manage.py runserver         # http://127.0.0.1:8000
```
Panel de administración: `http://127.0.0.1:8000/admin/`
(usuario de desarrollo creado: `admin` / `admin12345` — cambiar en producción).

## Despliegue
Guía completa para VPS de Hostinger (gunicorn + nginx + systemd + SSL):
[docs/deploy_hostinger.md](docs/deploy_hostinger.md). Variables de producción:
`DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`,
`DJANGO_CSRF_TRUSTED_ORIGINS` y `GEMINI_API_KEY`.

## Linting
```bash
uv run ruff check .
```

## Áreas de mejora
- Suite de tests automatizados (pytest) para el servicio de reservas.
- Notificación de errores críticos al desarrollador vía Telegram.
- Autenticación de clientes e historial de reservas.
- Cancelación/expiración de reservas no confirmadas por WhatsApp.
- Compresión/miniaturas de imágenes subidas.

## Copyright
Osliani Figueiras Saucedo
