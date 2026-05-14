from django.contrib import admin
from .models import CarAd, CarImage, CarTag, Favorite, Message, Profile, Review, SellerInfo


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'role', 'created_at')
    list_filter = ('role', 'city')
    search_fields = ('user__username', 'user__email', 'phone', 'city')


@admin.register(SellerInfo)
class SellerInfoAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'city', 'created_at')
    search_fields = ('full_name', 'phone', 'email', 'city')
    list_filter = ('city',)


class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 1


@admin.register(CarAd)
class CarAdAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'year', 'price', 'seller', 'status', 'removed', 'created_at')
    list_filter = ('status', 'removed', 'brand', 'transmission', 'year', 'tags')
    search_fields = ('brand', 'model', 'description', 'seller__full_name', 'seller__city')
    filter_horizontal = ('tags',)
    inlines = [CarImageInline]
    actions = ['make_active', 'make_hidden']

    @admin.action(description='Опубликовать выбранные объявления')
    def make_active(self, request, queryset):
        queryset.update(status='active', removed=False)

    @admin.action(description='Скрыть выбранные объявления')
    def make_hidden(self, request, queryset):
        queryset.update(status='hidden')


@admin.register(CarTag)
class CarTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CarImage)
class CarImageAdmin(admin.ModelAdmin):
    list_display = ('car_ad', 'is_main', 'uploaded_at')
    list_filter = ('is_main',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'car_ad', 'created_at')
    search_fields = ('user__username', 'car_ad__brand', 'car_ad__model')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('buyer_name', 'buyer_email', 'seller', 'car_ad', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('buyer_name', 'buyer_email', 'text', 'car_ad__brand', 'car_ad__model')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'seller', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('buyer__username', 'seller__full_name', 'comment')
