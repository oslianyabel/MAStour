# Reglas de negocio — Gestión de Excursiones

## Excursiones
- Un paquete turístico tiene precio de adultos y precio de niños (hasta 12 años).
- Cada excursión pertenece a una categoría (ej. Playa, Río) y a una localidad de destino.
- Puede tener fotos del destino, fotos del transporte, videos, coordenadas para mapa y actividades opcionales.

## Salidas (Slots)
- Cada salida pertenece a una excursión y tiene fecha, capacidad, guía, ofertas gastronómicas,
  dirección de pago, teléfono de contacto, hora de salida y hora de retorno.
- El punto de recogida se define **después** de vender toda la capacidad; hasta entonces el
  frontend muestra "por definir". El admin marca visualmente las salidas agotadas que necesitan
  punto de recogida.

## Reservas
- Una reserva pertenece a una salida e indica cantidad de adultos, cantidad de niños (hasta 12),
  dirección, nombre y teléfono del representante.
- **Validación de capacidad**: la suma de plazas reservadas (adultos + niños) nunca puede superar
  la capacidad de la salida. La creación de la reserva bloquea la fila del slot
  (`select_for_update`) para evitar sobreventa con reservas concurrentes.
- Una reserva debe incluir al menos 1 plaza y al menos 1 adulto.
- Tras completar la reserva, el cliente es redirigido al chat de WhatsApp (`wa.me`) del teléfono
  de contacto de la salida, con los datos de la reserva prellenados en el mensaje.

## Frontend
- Solo se muestran excursiones activas con salidas desde la fecha actual en adelante.
- Diseño responsive, mobile-first.

## Localidades semilla
Topes, Trinidad, Santa Clara, Cienfuegos, Yaguajay, Cabaiguan, Sancti Spiritus,
Peninsula de Trinidad.

## Categorías semilla
Playa, Río.
