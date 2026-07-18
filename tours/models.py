import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

HAVANA_TZ = ZoneInfo('America/Havana')


class Category(models.Model):
    """Excursion category, e.g. playa, rio."""

    name: models.CharField = models.CharField('nombre', max_length=100, unique=True)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Location(models.Model):
    """Locality used as destination or pickup point area."""

    name: models.CharField = models.CharField('nombre', max_length=100, unique=True)

    class Meta:
        verbose_name = 'localidad'
        verbose_name_plural = 'localidades'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Guide(models.Model):
    """Tour guide assigned to a slot."""

    class Sex(models.TextChoices):
        MALE = 'M', 'Masculino'
        FEMALE = 'F', 'Femenino'

    name: models.CharField = models.CharField('nombre', max_length=150)
    photo: models.ImageField = models.ImageField('foto', upload_to='guides/', blank=True)
    age: models.PositiveIntegerField = models.PositiveIntegerField('edad')
    sex: models.CharField = models.CharField('sexo', max_length=1, choices=Sex.choices)

    class Meta:
        verbose_name = 'guía'
        verbose_name_plural = 'guías'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class GastronomicOffer(models.Model):
    """Food/drink offer available on a slot."""

    name: models.CharField = models.CharField('nombre', max_length=150)
    image: models.ImageField = models.ImageField('imagen', upload_to='gastronomic_offers/', blank=True)
    price: models.DecimalField = models.DecimalField(
        'precio', max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))]
    )

    class Meta:
        verbose_name = 'oferta gastronómica'
        verbose_name_plural = 'ofertas gastronómicas'
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} (${self.price})'


class Excursion(models.Model):
    """Tour package offered to clients."""

    name: models.CharField = models.CharField('nombre', max_length=200)
    description: models.TextField = models.TextField('descripción', blank=True)
    adult_price: models.DecimalField = models.DecimalField(
        'precio adultos', max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))]
    )
    child_price: models.DecimalField = models.DecimalField(
        'precio niños (hasta 12 años)',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    destination: models.ForeignKey = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name='excursions', verbose_name='lugar de destino'
    )
    category: models.ForeignKey = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='excursions', verbose_name='categoría'
    )
    latitude: models.DecimalField = models.DecimalField(
        'latitud', max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude: models.DecimalField = models.DecimalField(
        'longitud', max_digits=9, decimal_places=6, null=True, blank=True
    )
    is_active: models.BooleanField = models.BooleanField('activa', default=True)

    class Meta:
        verbose_name = 'excursión'
        verbose_name_plural = 'excursiones'
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} — {self.destination}'

    @property
    def has_map(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    @property
    def cover_photo(self) -> 'ExcursionPhoto | None':
        return self.photos.first()


class OptionalActivity(models.Model):
    """Optional activity offered inside an excursion."""

    excursion: models.ForeignKey = models.ForeignKey(
        Excursion, on_delete=models.CASCADE, related_name='optional_activities', verbose_name='excursión'
    )
    name: models.CharField = models.CharField('nombre', max_length=200)
    description: models.TextField = models.TextField('descripción', blank=True)
    price: models.DecimalField = models.DecimalField(
        'precio',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
    )

    class Meta:
        verbose_name = 'actividad opcional'
        verbose_name_plural = 'actividades opcionales'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class ExcursionPhoto(models.Model):
    """Photo of the destination or the transport of an excursion."""

    class PhotoType(models.TextChoices):
        DESTINATION = 'destination', 'Destino'
        TRANSPORT = 'transport', 'Transporte'

    excursion: models.ForeignKey = models.ForeignKey(
        Excursion, on_delete=models.CASCADE, related_name='photos', verbose_name='excursión'
    )
    image: models.ImageField = models.ImageField('imagen', upload_to='excursions/photos/')
    photo_type: models.CharField = models.CharField(
        'tipo', max_length=20, choices=PhotoType.choices, default=PhotoType.DESTINATION
    )
    caption: models.CharField = models.CharField('descripción', max_length=200, blank=True)

    class Meta:
        verbose_name = 'foto'
        verbose_name_plural = 'fotos'
        ordering = ['photo_type', 'id']

    def __str__(self) -> str:
        return f'{self.get_photo_type_display()} — {self.excursion.name}'


class ExcursionVideo(models.Model):
    """Video of an excursion: an uploaded file or an external URL."""

    excursion: models.ForeignKey = models.ForeignKey(
        Excursion, on_delete=models.CASCADE, related_name='videos', verbose_name='excursión'
    )
    video_file: models.FileField = models.FileField(
        'archivo de video', upload_to='excursions/videos/', blank=True
    )
    video_url: models.URLField = models.URLField(
        'URL del video', blank=True, help_text='Alternativa al archivo: enlace de YouTube u otro.'
    )
    title: models.CharField = models.CharField('título', max_length=200, blank=True)

    class Meta:
        verbose_name = 'video'
        verbose_name_plural = 'videos'

    def __str__(self) -> str:
        return self.title or f'Video de {self.excursion.name}'


class PickupPoint(models.Model):
    """Pickup point, defined once a slot sells out its capacity."""

    location: models.ForeignKey = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name='pickup_points', verbose_name='localidad'
    )
    name: models.CharField = models.CharField('nombre', max_length=200)
    latitude: models.DecimalField = models.DecimalField(
        'latitud', max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude: models.DecimalField = models.DecimalField(
        'longitud', max_digits=9, decimal_places=6, null=True, blank=True
    )
    image: models.ImageField = models.ImageField('imagen', upload_to='pickup_points/', blank=True)

    class Meta:
        verbose_name = 'punto de recogida'
        verbose_name_plural = 'puntos de recogida'
        ordering = ['location__name', 'name']

    def __str__(self) -> str:
        return f'{self.name} ({self.location})'


class Slot(models.Model):
    """A scheduled departure of an excursion with limited capacity."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        COMPLETED = 'completed', 'Completada'

    excursion: models.ForeignKey = models.ForeignKey(
        Excursion, on_delete=models.CASCADE, related_name='slots', verbose_name='excursión'
    )
    date: models.DateField = models.DateField('fecha')
    capacity: models.PositiveIntegerField = models.PositiveIntegerField(
        'capacidad', validators=[MinValueValidator(1)]
    )
    guide: models.ForeignKey = models.ForeignKey(
        Guide, on_delete=models.PROTECT, related_name='slots', verbose_name='guía'
    )
    gastronomic_offers: models.ManyToManyField = models.ManyToManyField(
        GastronomicOffer, blank=True, related_name='slots', verbose_name='ofertas gastronómicas'
    )
    payment_address: models.CharField = models.CharField('dirección de pago', max_length=255)
    contact_phone: models.CharField = models.CharField(
        'teléfono de contacto',
        max_length=20,
        help_text='Con código de país, ej. +5352123456. Se usa para el chat de WhatsApp.',
    )
    departure_time: models.TimeField = models.TimeField('hora de salida')
    return_time: models.TimeField = models.TimeField('hora de retorno')
    pickup_point: models.ForeignKey = models.ForeignKey(
        PickupPoint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='slots',
        verbose_name='punto de recogida',
        help_text='Se define luego de tener todas las capacidades vendidas.',
    )
    status: models.CharField = models.CharField(
        'estado',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text='Pasa a "Completada" automáticamente cuando vence la hora de retorno (hora de La Habana).',
    )

    class Meta:
        verbose_name = 'salida (slot)'
        verbose_name_plural = 'salidas (slots)'
        ordering = ['date', 'departure_time']
        constraints = [
            models.UniqueConstraint(
                fields=['excursion', 'date', 'departure_time'], name='unique_slot_departure'
            )
        ]

    def __str__(self) -> str:
        return f'{self.excursion.name} — {self.date:%d/%m/%Y} {self.departure_time:%H:%M}'

    @property
    def seats_taken(self) -> int:
        aggregate = self.reservations.aggregate(
            total=models.Sum(models.F('adults_count') + models.F('children_count'))
        )
        return aggregate['total'] or 0

    @property
    def seats_available(self) -> int:
        return max(self.capacity - self.seats_taken, 0)

    @property
    def is_sold_out(self) -> bool:
        return self.seats_available == 0

    @property
    def whatsapp_phone(self) -> str:
        """Contact phone normalized to digits only, as required by wa.me links."""
        return ''.join(character for character in self.contact_phone if character.isdigit())

    @property
    def return_datetime(self) -> datetime.datetime:
        """Return date+time of the slot as an aware datetime in Havana time."""
        naive = datetime.datetime.combine(self.date, self.return_time)
        return naive.replace(tzinfo=HAVANA_TZ)

    @property
    def is_past(self) -> bool:
        """True once the slot's return time (Havana) has already passed."""
        return timezone.now() >= self.return_datetime


class Memory(models.Model):
    """Photo album of a completed slot, shown on the past-excursions page."""

    slot: models.OneToOneField = models.OneToOneField(
        Slot,
        on_delete=models.CASCADE,
        related_name='memory',
        verbose_name='salida',
        limit_choices_to={'status': Slot.Status.COMPLETED},
        help_text='Solo se puede asociar a salidas completadas.',
    )
    title: models.CharField = models.CharField('título', max_length=200, blank=True)
    description: models.TextField = models.TextField('descripción', blank=True)
    created_at: models.DateTimeField = models.DateTimeField('creado', auto_now_add=True)

    class Meta:
        verbose_name = 'recuerdo'
        verbose_name_plural = 'recuerdos'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title or f'Recuerdos de {self.slot}'


class MemoryImage(models.Model):
    """Single image inside a memory album."""

    memory: models.ForeignKey = models.ForeignKey(
        Memory, on_delete=models.CASCADE, related_name='images', verbose_name='recuerdo'
    )
    image: models.ImageField = models.ImageField('imagen', upload_to='memories/')
    caption: models.CharField = models.CharField('descripción', max_length=200, blank=True)

    class Meta:
        verbose_name = 'imagen del recuerdo'
        verbose_name_plural = 'imágenes del recuerdo'
        ordering = ['id']

    def __str__(self) -> str:
        return self.caption or f'Imagen #{self.pk}'


class Faq(models.Model):
    """Frequently asked question shown on the FAQ page, managed from the admin."""

    question: models.CharField = models.CharField('pregunta', max_length=300)
    answer: models.TextField = models.TextField('respuesta')
    order: models.PositiveIntegerField = models.PositiveIntegerField('orden', default=0)
    is_active: models.BooleanField = models.BooleanField('activa', default=True)

    class Meta:
        verbose_name = 'pregunta frecuente'
        verbose_name_plural = 'preguntas frecuentes'
        ordering = ['order', 'id']

    def __str__(self) -> str:
        return self.question


class SocialLink(models.Model):
    """Social network link shown in the site footer, managed from the admin."""

    class Platform(models.TextChoices):
        INSTAGRAM = 'instagram', 'Instagram'
        FACEBOOK = 'facebook', 'Facebook'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        YOUTUBE = 'youtube', 'YouTube'
        X = 'x', 'X'
        TELEGRAM = 'telegram', 'Telegram'

    platform: models.CharField = models.CharField(
        'plataforma', max_length=20, choices=Platform.choices, unique=True
    )
    url: models.URLField = models.URLField(
        'enlace', help_text='URL del perfil, ej. https://instagram.com/mastour'
    )
    is_active: models.BooleanField = models.BooleanField('activo', default=True)

    class Meta:
        verbose_name = 'red social'
        verbose_name_plural = 'redes sociales'
        ordering = ['platform']

    def __str__(self) -> str:
        return self.get_platform_display()


class TeamMember(models.Model):
    """Team member shown on the about-us page, managed from the admin."""

    name: models.CharField = models.CharField('nombre', max_length=150)
    role: models.CharField = models.CharField('cargo', max_length=150)
    quote: models.CharField = models.CharField(
        'frase', max_length=200, blank=True, help_text='Frase personal mostrada en cursiva.'
    )
    photo: models.ImageField = models.ImageField('foto', upload_to='team/', blank=True)
    order: models.PositiveIntegerField = models.PositiveIntegerField('orden', default=0)
    is_active: models.BooleanField = models.BooleanField('activo', default=True)

    class Meta:
        verbose_name = 'miembro del equipo'
        verbose_name_plural = 'miembros del equipo'
        ordering = ['order', 'id']

    def __str__(self) -> str:
        return f'{self.name} — {self.role}'


class Reservation(models.Model):
    """A client reservation for a slot."""

    slot: models.ForeignKey = models.ForeignKey(
        Slot, on_delete=models.CASCADE, related_name='reservations', verbose_name='salida'
    )
    adults_count: models.PositiveIntegerField = models.PositiveIntegerField(
        'cantidad de adultos', validators=[MinValueValidator(1)]
    )
    children_count: models.PositiveIntegerField = models.PositiveIntegerField(
        'cantidad de niños (hasta 12 años)', default=0
    )
    address: models.CharField = models.CharField('dirección', max_length=255)
    representative_name: models.CharField = models.CharField('nombre del representante', max_length=150)
    representative_phone: models.CharField = models.CharField('teléfono del representante', max_length=20)
    created_at: models.DateTimeField = models.DateTimeField('creada', auto_now_add=True)

    class Meta:
        verbose_name = 'reserva'
        verbose_name_plural = 'reservas'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.representative_name} — {self.slot}'

    @property
    def excursion(self) -> Excursion:
        return self.slot.excursion

    @property
    def total_people(self) -> int:
        return self.adults_count + self.children_count

    @property
    def total_price(self) -> Decimal:
        excursion = self.slot.excursion
        return excursion.adult_price * self.adults_count + excursion.child_price * self.children_count
