# AutoBoard — курсовая работа на Django

AutoBoard — веб-приложение для публикации и поиска объявлений о продаже автомобилей. Проект переработан из заготовки `django_hello_world`: сохранены приложение `helloapp`, сущности `CarAd`, `SellerInfo`, `CarImage`, CRUD объявлений и AJAX-проверки телефона/email, но добавлены требования курсовой на оценку «5».

## Что реализовано

- Django MVT: модели, views, templates.
- PostgreSQL вместо SQLite.
- 8+ таблиц: `Profile`, `SellerInfo`, `CarAd`, `CarImage`, `CarTag`, `Favorite`, `Message`, `Review`.
- Группы пользователей: `Buyer`, `Seller`, `Moderator`.
- Разные права для гостя, покупателя, продавца и модератора.
- Регистрация с подтверждением по token-ссылке на email.
- Расширение базовой модели пользователя через `Profile`.
- Личный кабинет и редактирование профиля.
- Создание, редактирование, удаление и модерация объявлений.
- Поиск, фильтрация по параметрам и тегам, пагинация.
- Cookie: недавно просмотренные объявления.
- Cache: статистика главной страницы и данные AJAX-статистики.
- JavaScript: динамический выбор модели авто, AJAX-проверка контактов, избранное без перезагрузки.
- Seed-команда создаёт базовых пользователей, роли, продавцов и теги без demo-объявлений: объявления и фотографии добавляются вручную через сайт.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Запустить PostgreSQL:

```bash
docker compose up -d
```

Применить миграции и создать базовые данные без demo-объявлений:

```bash
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

После `seed_data` доступны пользователи, а объявления можно добавить вручную через `/ads/add/`:

| Логин | Пароль | Роль |
|---|---|---|
| buyer_demo | DemoPass123! | Buyer |
| seller_demo | DemoPass123! | Seller |
| moderator_demo | DemoPass123! | Moderator |
| admin | AdminPass123! | superuser |

## Основные страницы

- `/` — главная страница.
- `/ads/` — список объявлений с поиском, фильтрами и пагинацией.
- `/ads/add/` — добавление объявления продавцом.
- `/profile/` — личный кабинет.
- `/moderation/` — панель модератора.
- `/register/` — регистрация с подтверждением.

## Тема для отчёта

**Разработка веб-приложения для размещения и поиска объявлений о продаже автомобилей на Django.**
