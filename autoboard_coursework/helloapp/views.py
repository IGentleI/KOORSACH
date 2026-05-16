import re

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Avg, Count, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.views.decorators.http import require_GET, require_POST
from django.conf import settings

from .forms import CarAdFilterForm, CarAdForm, MessageForm, ProfileForm, RegistrationForm, ReviewForm
from .models import CarAd, CarImage, CarTag, Favorite, Message, Review, SellerInfo
from .tokens import account_activation_token

User = get_user_model()
PHONE_REGEXP = re.compile(r'^\+?[0-9\s()\-]{10,20}$')
EMAIL_REGEXP = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$')



def _in_group(user, group_name):
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def _is_seller(user):
    return _in_group(user, 'Seller') or user.is_staff


def _is_moderator(user):
    return _in_group(user, 'Moderator') or user.is_staff


def _ensure_group(user, group_name):
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)


def _get_or_create_seller(user, cleaned_data):
    full_name = f"{cleaned_data['seller_last_name']} {cleaned_data['seller_first_name']} {cleaned_data.get('seller_middle_name', '')}".strip()
    seller, _ = SellerInfo.objects.get_or_create(
        user=user,
        defaults={
            'full_name': full_name,
            'phone': cleaned_data['seller_phone'],
            'email': cleaned_data.get('seller_email') or user.email,
            'city': cleaned_data['seller_city'],
        },
    )
    seller.full_name = full_name
    seller.phone = cleaned_data['seller_phone']
    seller.email = cleaned_data.get('seller_email') or user.email
    seller.city = cleaned_data['seller_city']
    seller.save()
    return seller


def _exclude_current_seller(queryset, car_id):
    if not car_id:
        return queryset
    try:
        current_car = CarAd.objects.select_related('seller').get(pk=int(car_id))
        return queryset.exclude(pk=current_car.seller_id)
    except (TypeError, ValueError, CarAd.DoesNotExist):
        return queryset


def _seller_phone_exists(phone, car_id=None):
    return _exclude_current_seller(SellerInfo.objects.filter(phone=phone), car_id).exists()


def _seller_email_exists(email, car_id=None):
    if not email:
        return False
    return _exclude_current_seller(SellerInfo.objects.filter(email__iexact=email), car_id).exists()


def _add_contact_duplicate_errors(form, car_id=None, user=None):
    phone = form.cleaned_data.get('seller_phone', '').strip()
    email = form.cleaned_data.get('seller_email', '').strip()
    has_errors = False

    phone_qs = SellerInfo.objects.filter(phone=phone)
    email_qs = SellerInfo.objects.filter(email__iexact=email) if email else SellerInfo.objects.none()
    if user and user.is_authenticated:
        phone_qs = phone_qs.exclude(user=user)
        email_qs = email_qs.exclude(user=user)
    phone_qs = _exclude_current_seller(phone_qs, car_id)
    email_qs = _exclude_current_seller(email_qs, car_id)

    if phone and phone_qs.exists():
        form.add_error('seller_phone', 'Такой телефон уже используется другим продавцом.')
        has_errors = True
    if email and email_qs.exists():
        form.add_error('seller_email', 'Такой email уже используется другим продавцом.')
        has_errors = True
    return has_errors


def index(request):
    stats = cache.get('index_stats')
    if stats is None:
        active_ads = CarAd.objects.filter(removed=False, status='active')
        stats = {
            'total_ads': active_ads.count(),
            'total_sellers': SellerInfo.objects.count(),
            'average_price': int(active_ads.aggregate(value=Avg('price'))['value'] or 0),
            'total_reviews': Review.objects.count(),
        }
        cache.set('index_stats', stats, 60)

    latest_ads = (
        CarAd.objects.filter(removed=False, status='active')
        .select_related('seller')
        .prefetch_related('images', 'tags')[:6]
    )
    popular_tags = cache.get('popular_tags')
    if popular_tags is None:
        popular_tags = list(CarTag.objects.annotate(total=Count('car_ads')).order_by('-total', 'name')[:8])
        cache.set('popular_tags', popular_tags, 300)

    return render(request, 'helloapp/index.html', {
        'stats': stats,
        'latest_ads': latest_ads,
        'popular_tags': popular_tags,
    })


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.is_active = False
            user.save()
            profile = user.profile
            profile.phone = form.cleaned_data['phone']
            profile.city = form.cleaned_data['city']
            profile.role = 'buyer'
            profile.save()
            _ensure_group(user, 'Buyer')

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            activation_url = request.build_absolute_uri(reverse('helloapp:activate', args=[uid, token]))
            send_mail(
                'Подтверждение регистрации AutoBoard',
                f'Здравствуйте! Для подтверждения регистрации перейдите по ссылке:\n{activation_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'Регистрация создана. Ссылка подтверждения отправлена на email и продублирована в консоли.')
            return render(request, 'helloapp/registration_done.html', {'activation_url': activation_url})
    else:
        form = RegistrationForm()
    return render(request, 'helloapp/register.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, 'Аккаунт подтверждён. Добро пожаловать!')
        return redirect('helloapp:index')

    messages.error(request, 'Ссылка подтверждения недействительна или устарела.')
    return redirect('helloapp:register')


@login_required
def profile(request):
    my_ads = CarAd.objects.filter(owner=request.user, removed=False).select_related('seller')[:10]
    favorites = Favorite.objects.filter(user=request.user).select_related('car_ad', 'car_ad__seller')[:10]
    incoming_messages = Message.objects.filter(seller__user=request.user).select_related('car_ad')[:10]
    return render(request, 'helloapp/profile.html', {
        'my_ads': my_ads,
        'favorites': favorites,
        'incoming_messages': incoming_messages,
    })


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('helloapp:profile')
    else:
        form = ProfileForm(instance=request.user.profile, user=request.user)
    return render(request, 'helloapp/profile_edit.html', {'form': form})


@login_required
def become_seller(request):
    _ensure_group(request.user, 'Seller')
    request.user.profile.role = 'seller'
    request.user.profile.save()
    messages.success(request, 'Теперь вы продавец и можете создавать объявления.')
    return redirect('helloapp:car_ad_form')


def car_ad_list(request):
    form = CarAdFilterForm(request.GET or None)
    car_ads = (
        CarAd.objects.filter(removed=False, status='active')
        .select_related('seller')
        .prefetch_related('images', 'tags')
    )

    if form.is_valid():
        data = form.cleaned_data
        q = data.get('q')
        if q:
            car_ads = car_ads.filter(Q(brand__icontains=q) | Q(model__icontains=q) | Q(description__icontains=q))
        if data.get('brand'):
            car_ads = car_ads.filter(brand__icontains=data['brand'])
        if data.get('city'):
            car_ads = car_ads.filter(seller__city__icontains=data['city'])
        if data.get('min_price') is not None:
            car_ads = car_ads.filter(price__gte=data['min_price'])
        if data.get('max_price') is not None:
            car_ads = car_ads.filter(price__lte=data['max_price'])
        if data.get('min_year'):
            car_ads = car_ads.filter(year__gte=data['min_year'])
        if data.get('transmission'):
            car_ads = car_ads.filter(transmission=data['transmission'])
        if data.get('tag'):
            car_ads = car_ads.filter(tags__slug=data['tag'])

    from django.core.paginator import Paginator
    paginator = Paginator(car_ads.distinct(), 6)
    page_obj = paginator.get_page(request.GET.get('page'))
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('car_ad_id', flat=True))

    return render(request, 'helloapp/car_ad_list.html', {
        'form': form,
        'page_obj': page_obj,
        'car_ads': page_obj.object_list,
        'tags': CarTag.objects.all(),
        'favorite_ids': favorite_ids,
    })


def car_ad_detail(request, pk):
    car_ad = get_object_or_404(
        CarAd.objects.select_related('seller', 'owner').prefetch_related('images', 'tags'),
        pk=pk,
        removed=False,
    )
    if car_ad.status != 'active' and not (_is_moderator(request.user) or car_ad.owner == request.user):
        return HttpResponseForbidden('Объявление пока не опубликовано.')

    CarAd.objects.filter(pk=pk).update(views_count=car_ad.views_count + 1)
    recently_viewed = request.COOKIES.get('recently_viewed_ads', '')
    ids = [item for item in recently_viewed.split(',') if item]
    ids = [str(pk)] + [item for item in ids if item != str(pk)]
    ids = ids[:5]

    message_form = MessageForm(user=request.user)
    review_form = ReviewForm()
    is_favorite = request.user.is_authenticated and Favorite.objects.filter(user=request.user, car_ad=car_ad).exists()
    response = render(request, 'helloapp/car_ad_detail.html', {
        'car_ad': car_ad,
        'images': car_ad.images.all(),
        'main_image': car_ad.main_image,
        'message_form': message_form,
        'review_form': review_form,
        'is_favorite': is_favorite,
    })
    response.set_cookie('recently_viewed_ads', ','.join(ids), max_age=60 * 60 * 24 * 30)
    return response


@login_required
def car_ad_form(request):
    if not _is_seller(request.user):
        messages.warning(request, 'Чтобы добавлять объявления, сначала получите роль продавца.')
        return redirect('helloapp:become_seller')

    if request.method == 'POST':
        form = CarAdForm(request.POST, request.FILES, user=request.user)
        if form.is_valid() and not _add_contact_duplicate_errors(form, user=request.user):
            seller = _get_or_create_seller(request.user, form.cleaned_data)
            car_ad = form.save(commit=False)
            car_ad.owner = request.user
            car_ad.seller = seller
            car_ad.status = 'pending'
            car_ad.save()
            form.save_m2m()
            if request.FILES.get('car_image'):
                CarImage.objects.create(car_ad=car_ad, image=request.FILES['car_image'], is_main=True)
            cache.delete('index_stats')
            messages.success(request, 'Объявление отправлено на модерацию.')
            return redirect('helloapp:car_ad_detail', pk=car_ad.pk)
        messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = CarAdForm(user=request.user)

    return render(request, 'helloapp/car_ad_form.html', {
        'form': form,
        'car_models': CarAdForm.CAR_MODELS,
    })


@login_required
def car_ad_edit(request, pk):
    car_ad = get_object_or_404(CarAd, pk=pk, removed=False)
    if car_ad.owner != request.user and not _is_moderator(request.user):
        return HttpResponseForbidden('Можно редактировать только свои объявления.')

    seller = car_ad.seller
    if request.method == 'POST':
        form = CarAdForm(request.POST, request.FILES, instance=car_ad, user=request.user)
        if form.is_valid() and not _add_contact_duplicate_errors(form, car_ad.id, request.user):
            seller = _get_or_create_seller(request.user, form.cleaned_data)
            car_ad = form.save(commit=False)
            car_ad.seller = seller
            if not _is_moderator(request.user):
                car_ad.status = 'pending'
            car_ad.save()
            form.save_m2m()
            if request.FILES.get('car_image'):
                CarImage.objects.filter(car_ad=car_ad, is_main=True).update(is_main=False)
                CarImage.objects.create(car_ad=car_ad, image=request.FILES['car_image'], is_main=True)
            cache.delete('index_stats')
            messages.success(request, 'Объявление обновлено.')
            return redirect('helloapp:car_ad_detail', pk=car_ad.pk)
    else:
        parts = seller.full_name.split()
        initial = {
            'seller_last_name': parts[0] if len(parts) > 0 else '',
            'seller_first_name': parts[1] if len(parts) > 1 else '',
            'seller_middle_name': parts[2] if len(parts) > 2 else '',
            'seller_phone': seller.phone,
            'seller_email': seller.email,
            'seller_city': seller.city,
        }
        form = CarAdForm(instance=car_ad, initial=initial, user=request.user)

    return render(request, 'helloapp/car_ad_form.html', {
        'form': form,
        'car_ad': car_ad,
        'is_edit': True,
        'car_models': CarAdForm.CAR_MODELS,
    })


@login_required
def car_ad_delete(request, pk):
    car_ad = get_object_or_404(CarAd, pk=pk)
    if car_ad.owner != request.user and not _is_moderator(request.user):
        return HttpResponseForbidden('Можно удалять только свои объявления.')
    if request.method == 'POST':
        car_ad.removed = True
        car_ad.status = 'hidden'
        car_ad.save(update_fields=['removed', 'status'])
        cache.delete('index_stats')
        messages.success(request, 'Объявление скрыто из каталога.')
        return redirect('helloapp:car_ad_list')
    return render(request, 'helloapp/car_ad_confirm_delete.html', {'car_ad': car_ad})


@login_required
@require_POST
def favorite_toggle(request, pk):
    car_ad = get_object_or_404(CarAd, pk=pk, removed=False)
    favorite, created = Favorite.objects.get_or_create(user=request.user, car_ad=car_ad)
    if not created:
        favorite.delete()
    return JsonResponse({'is_favorite': created, 'count': car_ad.favorites.count()})


@login_required
def contact_seller(request, pk):
    car_ad = get_object_or_404(CarAd, pk=pk, removed=False, status='active')
    if request.method == 'POST':
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.car_ad = car_ad
            message.seller = car_ad.seller
            message.sender = request.user
            message.save()
            messages.success(request, 'Сообщение отправлено продавцу.')
            return redirect('helloapp:car_ad_detail', pk=pk)
    return redirect('helloapp:car_ad_detail', pk=pk)


@login_required
@user_passes_test(_is_moderator)
def moderation_list(request):
    ads = CarAd.objects.filter(removed=False).select_related('seller', 'owner').order_by('-created_at')
    return render(request, 'helloapp/moderation_list.html', {'ads': ads})


@login_required
@user_passes_test(_is_moderator)
def moderation_update(request, pk, status):
    if status not in {'active', 'rejected', 'hidden'}:
        messages.error(request, 'Некорректный статус.')
        return redirect('helloapp:moderation_list')
    car_ad = get_object_or_404(CarAd, pk=pk)
    car_ad.status = status
    car_ad.removed = status == 'hidden'
    car_ad.save(update_fields=['status', 'removed'])
    cache.delete('index_stats')
    messages.success(request, f'Статус объявления изменён: {car_ad.get_status_display()}.')
    return redirect('helloapp:moderation_list')


@require_GET
def ajax_check_phone(request):
    phone = request.GET.get('phone', '').strip()
    car_id = request.GET.get('car_id', '').strip()
    if not phone:
        return JsonResponse({'valid': False, 'exists': False, 'message': 'Введите телефон для проверки.'})
    if not PHONE_REGEXP.match(phone):
        return JsonResponse({'valid': False, 'exists': False, 'message': 'Телефон не соответствует формату.'})
    exists = _seller_phone_exists(phone, car_id)
    return JsonResponse({'valid': True, 'exists': exists, 'message': 'Телефон уже есть в базе.' if exists else 'Телефон свободен.'})


@require_GET
def ajax_check_email(request):
    email = request.GET.get('email', '').strip()
    car_id = request.GET.get('car_id', '').strip()
    if not email:
        return JsonResponse({'valid': True, 'exists': False, 'message': 'Email не указан — поле можно оставить пустым.'})
    if not EMAIL_REGEXP.match(email):
        return JsonResponse({'valid': False, 'exists': False, 'message': 'Email не соответствует формату.'})
    exists = _seller_email_exists(email, car_id)
    return JsonResponse({'valid': True, 'exists': exists, 'message': 'Email уже есть в базе.' if exists else 'Email свободен.'})


@require_GET
def ajax_car_ad_stats(request):
    stats = cache.get('ajax_car_ad_stats')
    if stats is None:
        active_ads = CarAd.objects.filter(removed=False, status='active')
        avg_price = active_ads.aggregate(value=Avg('price'))['value']
        latest_car = active_ads.select_related('seller').order_by('-created_at').first()
        stats = {
            'total_ads': active_ads.count(),
            'total_sellers': active_ads.values('seller_id').distinct().count(),
            'negotiable_ads': active_ads.filter(is_negotiable=True).count(),
            'average_price': int(avg_price) if avg_price else 0,
            'latest_ad': f'{latest_car.brand} {latest_car.model}' if latest_car else 'Нет объявлений',
            'latest_ad_created_at': latest_car.created_at.strftime('%d.%m.%Y %H:%M') if latest_car else '-',
        }
        cache.set('ajax_car_ad_stats', stats, 60)
    return JsonResponse(stats)


@require_GET
def ajax_latest_car_ads(request):
    latest_ads = (
        CarAd.objects.filter(removed=False, status='active')
        .select_related('seller')
        .order_by('-created_at')[:3]
    )
    items = []
    for car in latest_ads:
        items.append({
            'id': car.id,
            'title': f'{car.brand} {car.model}, {car.year}',
            'seller': car.seller.full_name,
            'city': car.seller.city,
            'price': int(car.price),
            'created_at': car.created_at.strftime('%d.%m.%Y %H:%M'),
            'detail_url': reverse('helloapp:car_ad_detail', args=[car.id]),
        })
    return JsonResponse({'items': items})
