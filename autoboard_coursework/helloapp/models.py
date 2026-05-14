from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Profile(models.Model):
    """Расширение базовой модели пользователя для критерия оценки 5."""

    ROLE_CHOICES = [
        ('buyer', 'Покупатель'),
        ('seller', 'Продавец'),
        ('moderator', 'Модератор'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField('Телефон', max_length=30, blank=True)
    city = models.CharField('Город', max_length=80, blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    role = models.CharField('Роль профиля', max_length=20, choices=ROLE_CHOICES, default='buyer')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль {self.user.username}'


class SellerInfo(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_info',
        verbose_name='Пользователь-продавец',
        null=True,
        blank=True,
    )
    full_name = models.CharField('ФИО продавца', max_length=160)
    phone = models.CharField('Телефон', max_length=30, unique=True)
    email = models.EmailField('Email', blank=True)
    city = models.CharField('Город', max_length=80)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Продавец'
        verbose_name_plural = 'Продавцы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} ({self.city})'


class CarTag(models.Model):
    name = models.CharField('Название', max_length=40, unique=True)
    slug = models.SlugField('Slug', max_length=60, unique=True)

    class Meta:
        verbose_name = 'Тег автомобиля'
        verbose_name_plural = 'Теги автомобилей'
        ordering = ['name']

    def __str__(self):
        return self.name


class CarAd(models.Model):
    TRANSMISSION_CHOICES = [
        ('manual', 'Механика'),
        ('automatic', 'Автомат'),
        ('robot', 'Робот'),
        ('variator', 'Вариатор'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('pending', 'На модерации'),
        ('active', 'Опубликовано'),
        ('rejected', 'Отклонено'),
        ('hidden', 'Скрыто'),
        ('sold', 'Продано'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='car_ads',
        verbose_name='Автор объявления',
        null=True,
        blank=True,
    )
    seller = models.ForeignKey(SellerInfo, on_delete=models.CASCADE, related_name='cars', verbose_name='Продавец')
    brand = models.CharField('Марка', max_length=60)
    model = models.CharField('Модель', max_length=60)
    year = models.PositiveIntegerField('Год выпуска', validators=[MinValueValidator(1980), MaxValueValidator(2030)])
    price = models.DecimalField('Цена', max_digits=12, decimal_places=2)
    mileage = models.PositiveIntegerField('Пробег, км')
    engine_volume = models.DecimalField('Объём двигателя', max_digits=3, decimal_places=1)
    transmission = models.CharField('Коробка передач', max_length=20, choices=TRANSMISSION_CHOICES)
    color = models.CharField('Цвет', max_length=40)
    description = models.TextField('Описание')
    is_negotiable = models.BooleanField('Торг уместен', default=False)
    tags = models.ManyToManyField(CarTag, blank=True, related_name='car_ads', verbose_name='Теги')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    removed = models.BooleanField('Удалено', default=False)
    views_count = models.PositiveIntegerField('Просмотры', default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'removed']),
            models.Index(fields=['brand', 'model']),
            models.Index(fields=['price']),
            models.Index(fields=['year']),
        ]

    def __str__(self):
        return f'{self.brand} {self.model}, {self.year}'

    def get_absolute_url(self):
        return reverse('helloapp:car_ad_detail', args=[self.pk])

    @property
    def main_image(self):
        return self.images.filter(is_main=True).first() or self.images.first()


class CarImage(models.Model):
    car_ad = models.ForeignKey(CarAd, on_delete=models.CASCADE, related_name='images', verbose_name='Объявление')
    image = models.ImageField('Фотография', upload_to='cars/', blank=True, null=True)
    caption = models.CharField('Подпись', max_length=120, blank=True)
    is_main = models.BooleanField('Главное фото', default=False)
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)

    class Meta:
        verbose_name = 'Фотография автомобиля'
        verbose_name_plural = 'Фотографии автомобилей'
        ordering = ['-is_main', 'uploaded_at']

    def __str__(self):
        return f'Фото для {self.car_ad}'


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    car_ad = models.ForeignKey(CarAd, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'car_ad')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} → {self.car_ad}'


class Message(models.Model):
    car_ad = models.ForeignKey(CarAd, on_delete=models.CASCADE, related_name='messages', verbose_name='Объявление')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='sent_messages', null=True, blank=True)
    seller = models.ForeignKey(SellerInfo, on_delete=models.CASCADE, related_name='received_messages')
    buyer_name = models.CharField('Имя покупателя', max_length=100)
    buyer_email = models.EmailField('Email покупателя')
    text = models.TextField('Сообщение')
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField('Дата сообщения', auto_now_add=True)

    class Meta:
        verbose_name = 'Сообщение продавцу'
        verbose_name_plural = 'Сообщения продавцам'
        ordering = ['-created_at']

    def __str__(self):
        return f'Сообщение по {self.car_ad}'


class Review(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_left')
    seller = models.ForeignKey(SellerInfo, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField('Оценка', validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField('Комментарий')
    created_at = models.DateTimeField('Дата отзыва', auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = ('buyer', 'seller')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.rating}/5 для {self.seller}'
