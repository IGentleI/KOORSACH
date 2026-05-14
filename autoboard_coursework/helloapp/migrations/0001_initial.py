# Generated manually for the coursework package.
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CarTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40, unique=True, verbose_name='Название')),
                ('slug', models.SlugField(max_length=60, unique=True, verbose_name='Slug')),
            ],
            options={'verbose_name': 'Тег автомобиля', 'verbose_name_plural': 'Теги автомобилей', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=30, verbose_name='Телефон')),
                ('city', models.CharField(blank=True, max_length=80, verbose_name='Город')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Аватар')),
                ('role', models.CharField(choices=[('buyer', 'Покупатель'), ('seller', 'Продавец'), ('moderator', 'Модератор')], default='buyer', max_length=20, verbose_name='Роль профиля')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Профиль', 'verbose_name_plural': 'Профили'},
        ),
        migrations.CreateModel(
            name='SellerInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=160, verbose_name='ФИО продавца')),
                ('phone', models.CharField(max_length=30, unique=True, verbose_name='Телефон')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('city', models.CharField(max_length=80, verbose_name='Город')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='seller_info', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь-продавец')),
            ],
            options={'verbose_name': 'Продавец', 'verbose_name_plural': 'Продавцы', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='CarAd',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('brand', models.CharField(max_length=60, verbose_name='Марка')),
                ('model', models.CharField(max_length=60, verbose_name='Модель')),
                ('year', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1980), django.core.validators.MaxValueValidator(2030)], verbose_name='Год выпуска')),
                ('price', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Цена')),
                ('mileage', models.PositiveIntegerField(verbose_name='Пробег, км')),
                ('engine_volume', models.DecimalField(decimal_places=1, max_digits=3, verbose_name='Объём двигателя')),
                ('transmission', models.CharField(choices=[('manual', 'Механика'), ('automatic', 'Автомат'), ('robot', 'Робот'), ('variator', 'Вариатор')], max_length=20, verbose_name='Коробка передач')),
                ('color', models.CharField(max_length=40, verbose_name='Цвет')),
                ('description', models.TextField(verbose_name='Описание')),
                ('is_negotiable', models.BooleanField(default=False, verbose_name='Торг уместен')),
                ('status', models.CharField(choices=[('draft', 'Черновик'), ('pending', 'На модерации'), ('active', 'Опубликовано'), ('rejected', 'Отклонено'), ('hidden', 'Скрыто'), ('sold', 'Продано')], default='pending', max_length=20, verbose_name='Статус')),
                ('removed', models.BooleanField(default=False, verbose_name='Удалено')),
                ('views_count', models.PositiveIntegerField(default=0, verbose_name='Просмотры')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='car_ads', to=settings.AUTH_USER_MODEL, verbose_name='Автор объявления')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cars', to='helloapp.sellerinfo', verbose_name='Продавец')),
                ('tags', models.ManyToManyField(blank=True, related_name='car_ads', to='helloapp.cartag', verbose_name='Теги')),
            ],
            options={
                'verbose_name': 'Объявление',
                'verbose_name_plural': 'Объявления',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['status', 'removed'], name='helloapp_ca_status_1558a9_idx'),
                    models.Index(fields=['brand', 'model'], name='helloapp_ca_brand_56d04d_idx'),
                    models.Index(fields=['price'], name='helloapp_ca_price_79c3c0_idx'),
                    models.Index(fields=['year'], name='helloapp_ca_year_38130d_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='CarImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to='cars/', verbose_name='Фотография')),
                ('caption', models.CharField(blank=True, max_length=120, verbose_name='Подпись')),
                ('is_main', models.BooleanField(default=False, verbose_name='Главное фото')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')),
                ('car_ad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='helloapp.carad', verbose_name='Объявление')),
            ],
            options={'verbose_name': 'Фотография автомобиля', 'verbose_name_plural': 'Фотографии автомобилей', 'ordering': ['-is_main', 'uploaded_at']},
        ),
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')),
                ('car_ad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to='helloapp.carad')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Избранное', 'verbose_name_plural': 'Избранное', 'ordering': ['-created_at'], 'unique_together': {('user', 'car_ad')}},
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buyer_name', models.CharField(max_length=100, verbose_name='Имя покупателя')),
                ('buyer_email', models.EmailField(max_length=254, verbose_name='Email покупателя')),
                ('text', models.TextField(verbose_name='Сообщение')),
                ('is_read', models.BooleanField(default=False, verbose_name='Прочитано')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата сообщения')),
                ('car_ad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='helloapp.carad', verbose_name='Объявление')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to='helloapp.sellerinfo')),
                ('sender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Сообщение продавцу', 'verbose_name_plural': 'Сообщения продавцам', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Оценка')),
                ('comment', models.TextField(verbose_name='Комментарий')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата отзыва')),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews_left', to=settings.AUTH_USER_MODEL)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='helloapp.sellerinfo')),
            ],
            options={'verbose_name': 'Отзыв', 'verbose_name_plural': 'Отзывы', 'ordering': ['-created_at'], 'unique_together': {('buyer', 'seller')}},
        ),
    ]
