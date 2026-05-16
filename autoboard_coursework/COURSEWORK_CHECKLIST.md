# Соответствие критериям курсовой работы

| Критерий | Где реализовано |
|---|---|
| Django web-приложение | `myproject`, `helloapp` |
| MVT | `models.py`, `views.py`, `templates/` |
| ООП | Django models, forms, management command |
| 5+ таблиц | `Profile`, `SellerInfo`, `CarAd`, `CarImage`, `CarTag`, `Favorite`, `Message`, `Review` |
| PostgreSQL | `settings.py`, `docker-compose.yml`, `.env.example` |
| Разные группы пользователей | `Buyer`, `Seller`, `Moderator` в `seed_data.py`; группам назначены Django permissions, а доступ в `views.py` разделён для покупателя, продавца и модератора |
| Подтверждение регистрации | `register`, `activate`, `tokens.py` |
| Расширение User | модель `Profile` + signals |
| Формы не из админки | регистрация, профиль, объявление, сообщение продавцу, отзыв |
| Личный кабинет | `profile`, `profile_edit`, шаблоны профиля |
| 15+ записей | `python manage.py seed_data` |
| Пагинация | `car_ad_list` |
| Фильтрация | `CarAdFilterForm`, `car_ad_list` |
| Поиск | поле `q` в списке объявлений |
| Cookie | `recently_viewed_ads` в `car_ad_detail` |
| Cache | `index`, `ajax_car_ad_stats` |
| JavaScript | `static/helloapp/js/main.js` |
| Адаптивный дизайн | `static/helloapp/css/style.css` |

## Визуальное оформление

Фон сделан простым белым, без сложных декоративных градиентов и размытия, чтобы интерфейс выглядел как обычный учебный сайт.
