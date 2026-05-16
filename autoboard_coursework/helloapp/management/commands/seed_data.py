from random import choice

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from helloapp.models import CarAd, CarTag, SellerInfo


class Command(BaseCommand):
    help = 'Создаёт группы, пользователей, продавцов и теги для защиты курсовой без demo-объявлений.'

    def handle(self, *args, **options):
        deleted_ads, _ = CarAd.objects.all().delete()
        if deleted_ads:
            self.stdout.write(self.style.WARNING(f'Удалено объявлений и связанных фото: {deleted_ads}.'))

        buyer_group, _ = Group.objects.get_or_create(name='Buyer')
        seller_group, _ = Group.objects.get_or_create(name='Seller')
        moderator_group, _ = Group.objects.get_or_create(name='Moderator')

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
        SellerInfo.objects.get_or_create(
            user=seller_demo,
            defaults={
                'full_name': 'Пётр Продавец',
                'phone': '+79003000002',
                'email': 'seller_contact_demo@example.com',
                'city': seller_demo.profile.city,
            },
        )

        moderator, _ = User.objects.get_or_create(username='moderator_demo', defaults={'email': 'moderator@example.com', 'first_name': 'Мария', 'last_name': 'Модератор', 'is_staff': True, 'is_active': True})
        moderator.set_password('DemoPass123!')
        moderator.save()
        moderator.groups.add(moderator_group)
        moderator.profile.phone = '+79001000003'
        moderator.profile.city = 'Красноярск'
        moderator.profile.role = 'moderator'
        moderator.profile.save()

        tag_names = ['С пробегом', 'Автомат', 'Семейный', 'Экономичный', 'Полноприводный', 'Премиум', 'Для города', 'Для путешествий', 'Без ДТП', 'Один владелец', 'Новая резина', 'Торг', 'Кредит', 'Лизинг', 'Сервисная книжка', 'Зимний пакет', 'Камера', 'Парктроники']
        for name in tag_names:
            CarTag.objects.get_or_create(name=name, defaults={'slug': slugify(name, allow_unicode=True)})

        cities = ['Красноярск', 'Новосибирск', 'Москва', 'Санкт-Петербург', 'Томск', 'Иркутск']
        for i in range(1, 19):
            user, _ = User.objects.get_or_create(username=f'seller_{i}', defaults={'email': f'seller_{i}@example.com', 'first_name': f'Имя{i}', 'last_name': f'Продавец{i}', 'is_active': True})
            user.set_password('DemoPass123!')
            user.save()
            user.groups.add(buyer_group, seller_group)
            user.profile.phone = f'+79002000{i:03d}'
            user.profile.city = choice(cities)
            user.profile.role = 'seller'
            user.profile.save()
            SellerInfo.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': f'Продавец {i}',
                    'phone': f'+79003000{i:03d}',
                    'email': f'seller_contact_{i}@example.com',
                    'city': user.profile.city,
                },
            )

        self.stdout.write(self.style.SUCCESS('Базовые данные созданы без demo-объявлений. Объявления и фотографии можно добавить вручную через сайт.'))
        self.stdout.write(self.style.SUCCESS('Логины: admin/AdminPass123!, buyer_demo/DemoPass123!, seller_demo/DemoPass123!, moderator_demo/DemoPass123!'))
