from decimal import Decimal
from random import choice, randint, sample

from django.contrib.auth.models import Group, Permission, User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from helloapp.models import CarAd, CarImage, CarTag, Favorite, Message, Review, SellerInfo


GROUP_PERMISSIONS = {
    'Buyer': [
        'view_carad', 'view_cartag', 'add_favorite', 'delete_favorite',
        'add_message', 'view_message', 'add_review', 'view_review',
    ],
    'Seller': [
        'add_carad', 'change_carad', 'delete_carad', 'view_carad',
        'add_carimage', 'change_carimage', 'delete_carimage', 'view_carimage',
        'add_sellerinfo', 'change_sellerinfo', 'view_sellerinfo',
        'view_message', 'view_review',
    ],
    'Moderator': [
        'change_carad', 'delete_carad', 'view_carad',
        'change_carimage', 'delete_carimage', 'view_carimage',
        'change_sellerinfo', 'view_sellerinfo',
        'change_message', 'view_message',
        'change_review', 'delete_review', 'view_review',
    ],
}


def configure_group_permissions(groups):
    """Назначает демонстрационные Django permissions группам для защиты курсовой."""

    for group_name, codenames in GROUP_PERMISSIONS.items():
        permissions = Permission.objects.filter(codename__in=codenames)
        groups[group_name].permissions.set(permissions)


class Command(BaseCommand):
    help = 'Создаёт группы, пользователей и тестовые данные для защиты курсовой.'

    def handle(self, *args, **options):
        buyer_group, _ = Group.objects.get_or_create(name='Buyer')
        seller_group, _ = Group.objects.get_or_create(name='Seller')
        moderator_group, _ = Group.objects.get_or_create(name='Moderator')
        configure_group_permissions({
            'Buyer': buyer_group,
            'Seller': seller_group,
            'Moderator': moderator_group,
        })

        admin, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True, 'is_active': True})
        admin.set_password('AdminPass123!')
        admin.save()

        buyer, _ = User.objects.get_or_create(username='buyer_demo', defaults={'email': 'buyer@example.com', 'first_name': 'Иван', 'last_name': 'Покупатель', 'is_active': True})
        buyer.set_password('DemoPass123!')
        buyer.save()
        buyer.groups.add(buyer_group)
        buyer.profile.phone = '+79001000001'
        buyer.profile.city = 'Красноярск'
        buyer.profile.role = 'buyer'
        buyer.profile.save()

        seller_demo, _ = User.objects.get_or_create(username='seller_demo', defaults={'email': 'seller@example.com', 'first_name': 'Пётр', 'last_name': 'Продавец', 'is_active': True})
        seller_demo.set_password('DemoPass123!')
        seller_demo.save()
        seller_demo.groups.add(buyer_group, seller_group)
        seller_demo.profile.phone = '+79001000002'
        seller_demo.profile.city = 'Красноярск'
        seller_demo.profile.role = 'seller'
        seller_demo.profile.save()

        moderator, _ = User.objects.get_or_create(username='moderator_demo', defaults={'email': 'moderator@example.com', 'first_name': 'Мария', 'last_name': 'Модератор', 'is_staff': True, 'is_active': True})
        moderator.set_password('DemoPass123!')
        moderator.save()
        moderator.groups.add(moderator_group)
        moderator.profile.phone = '+79001000003'
        moderator.profile.city = 'Красноярск'
        moderator.profile.role = 'moderator'
        moderator.profile.save()

        tag_names = ['С пробегом', 'Автомат', 'Семейный', 'Экономичный', 'Полноприводный', 'Премиум', 'Для города', 'Для путешествий', 'Без ДТП', 'Один владелец', 'Новая резина', 'Торг', 'Кредит', 'Лизинг', 'Сервисная книжка', 'Зимний пакет', 'Камера', 'Парктроники']
        tags = []
        for name in tag_names:
            tag, _ = CarTag.objects.get_or_create(name=name, defaults={'slug': slugify(name, allow_unicode=True)})
            tags.append(tag)

        brands = {
            'Toyota': ['Camry', 'Corolla', 'RAV4', 'Land Cruiser'],
            'BMW': ['3 Series', '5 Series', 'X3', 'X5'],
            'Mercedes-Benz': ['C-Class', 'E-Class', 'GLA', 'GLE'],
            'Kia': ['Rio', 'Ceed', 'Sportage', 'Sorento'],
            'Hyundai': ['Solaris', 'Elantra', 'Tucson', 'Santa Fe'],
            'Lada': ['Granta', 'Vesta', 'Niva Travel', 'Largus'],
            'Volkswagen': ['Polo', 'Jetta', 'Tiguan', 'Touareg'],
        }
        cities = ['Красноярск', 'Новосибирск', 'Москва', 'Санкт-Петербург', 'Томск', 'Иркутск']
        transmissions = ['manual', 'automatic', 'robot', 'variator']
        colors = ['чёрный', 'белый', 'серебристый', 'синий', 'красный', 'серый']

        sellers = []
        for i in range(1, 19):
            user, _ = User.objects.get_or_create(username=f'seller_{i}', defaults={'email': f'seller_{i}@example.com', 'first_name': f'Имя{i}', 'last_name': f'Продавец{i}', 'is_active': True})
            user.set_password('DemoPass123!')
            user.save()
            user.groups.add(buyer_group, seller_group)
            user.profile.phone = f'+79002000{i:03d}'
            user.profile.city = choice(cities)
            user.profile.role = 'seller'
            user.profile.save()
            seller, _ = SellerInfo.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': f'Продавец {i}',
                    'phone': f'+79003000{i:03d}',
                    'email': f'seller_contact_{i}@example.com',
                    'city': user.profile.city,
                },
            )
            sellers.append(seller)

        for i in range(1, 25):
            brand = choice(list(brands.keys()))
            model = choice(brands[brand])
            seller = choice(sellers)
            car_ad, created = CarAd.objects.get_or_create(
                seller=seller,
                brand=brand,
                model=model,
                year=randint(2008, 2024),
                defaults={
                    'owner': seller.user,
                    'price': Decimal(randint(450_000, 7_000_000)),
                    'mileage': randint(5_000, 220_000),
                    'engine_volume': Decimal(choice(['1.4', '1.6', '2.0', '2.5', '3.0'])),
                    'transmission': choice(transmissions),
                    'color': choice(colors),
                    'description': 'Тестовое объявление для демонстрации курсовой работы: исправное состояние, документы готовы, возможен осмотр.',
                    'is_negotiable': bool(randint(0, 1)),
                    'status': 'active' if i % 5 else 'pending',
                    'views_count': randint(0, 500),
                },
            )
            car_ad.tags.set(sample(tags, k=randint(2, 4)))
            if not car_ad.images.exists():
                CarImage.objects.create(
                    car_ad=car_ad,
                    caption='Демо-фото',
                    is_main=True,
                    image=ContentFile(b'demo image placeholder', name=f'car_{car_ad.pk}.jpg'),
                )

        ads = list(CarAd.objects.all())
        users = list(User.objects.filter(username__startswith='seller_')) + [buyer]
        for idx, user in enumerate(users[:18]):
            Favorite.objects.get_or_create(user=user, car_ad=choice(ads))
            Message.objects.get_or_create(
                car_ad=choice(ads),
                sender=buyer,
                seller=choice(sellers),
                buyer_name='Иван Покупатель',
                buyer_email='buyer@example.com',
                text=f'Здравствуйте! Актуально ли объявление? Сообщение #{idx + 1}',
            )
            Review.objects.get_or_create(
                buyer=buyer,
                seller=sellers[idx % len(sellers)],
                defaults={'rating': randint(4, 5), 'comment': 'Продавец быстро ответил и подробно рассказал об автомобиле.'},
            )

        self.stdout.write(self.style.SUCCESS('Данные созданы. Логины: admin/AdminPass123!, buyer_demo/DemoPass123!, seller_demo/DemoPass123!, moderator_demo/DemoPass123!'))
