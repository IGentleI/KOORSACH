import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import CarAd, CarImage, Message, Profile, Review

PHONE_REGEXP = re.compile(r'^\+?[0-9\s()\-]{10,20}$')


class BootstrapFormMixin:
    def _init_bootstrap(self):
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = (css + ' form-check-input').strip()
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs['class'] = (css + ' tags-list').strip()
            else:
                field.widget.attrs['class'] = (css + ' form-control').strip()


class RegistrationForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(label='Email')
    first_name = forms.CharField(label='Имя', max_length=80)
    last_name = forms.CharField(label='Фамилия', max_length=80)
    phone = forms.CharField(label='Телефон', max_length=30)
    city = forms.CharField(label='Город', max_length=80)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'city', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_bootstrap()

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not PHONE_REGEXP.match(phone):
            raise forms.ValidationError('Телефон должен содержать 10–20 цифр и может начинаться с +.')
        return phone

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_bootstrap()


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    first_name = forms.CharField(label='Имя', max_length=80, required=False)
    last_name = forms.CharField(label='Фамилия', max_length=80, required=False)
    email = forms.EmailField(label='Email')

    class Meta:
        model = Profile
        fields = ['phone', 'city', 'avatar']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['first_name'].initial = self.user.first_name
        self.fields['last_name'].initial = self.user.last_name
        self.fields['email'].initial = self.user.email
        self._init_bootstrap()

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        if commit:
            self.user.save()
            profile.save()
        return profile


class CarAdFilterForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(label='Поиск', required=False, widget=forms.TextInput(attrs={'placeholder': 'Марка, модель или описание'}))
    brand = forms.CharField(label='Марка', required=False)
    city = forms.CharField(label='Город', required=False)
    min_price = forms.DecimalField(label='Цена от', required=False, min_value=0)
    max_price = forms.DecimalField(label='Цена до', required=False, min_value=0)
    min_year = forms.IntegerField(label='Год от', required=False, min_value=1980)
    transmission = forms.ChoiceField(label='Коробка', required=False, choices=[('', 'Любая')] + CarAd.TRANSMISSION_CHOICES)
    tag = forms.CharField(label='Тег', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_bootstrap()


CAR_MODELS = {
    'Toyota': ['Camry', 'Corolla', 'RAV4', 'Land Cruiser'],
    'BMW': ['3 Series', '5 Series', 'X3', 'X5'],
    'Mercedes-Benz': ['C-Class', 'E-Class', 'GLA', 'GLE'],
    'Kia': ['Rio', 'Ceed', 'Sportage', 'Sorento'],
    'Hyundai': ['Solaris', 'Elantra', 'Tucson', 'Santa Fe'],
    'Lada': ['Granta', 'Vesta', 'Niva Travel', 'Largus'],
    'Volkswagen': ['Polo', 'Jetta', 'Tiguan', 'Touareg'],
}


class CarAdForm(BootstrapFormMixin, forms.ModelForm):
    CAR_MODELS = CAR_MODELS

    seller_last_name = forms.CharField(label='Фамилия продавца', max_length=80)
    seller_first_name = forms.CharField(label='Имя продавца', max_length=80)
    seller_middle_name = forms.CharField(label='Отчество продавца', max_length=80, required=False)
    seller_phone = forms.CharField(label='Телефон продавца', max_length=30)
    seller_email = forms.EmailField(label='Email продавца', required=False)
    seller_city = forms.CharField(label='Город продавца', max_length=80)
    car_image = forms.ImageField(label='Главное фото', required=False)

    class Meta:
        model = CarAd
        fields = [
            'brand', 'model', 'year', 'price', 'mileage', 'engine_volume',
            'transmission', 'color', 'description', 'is_negotiable', 'tags'
        ]
        widgets = {
            'brand': forms.Select(choices=[('', 'Выберите марку')] + [(brand, brand) for brand in CAR_MODELS]),
            'model': forms.Select(choices=[('', 'Сначала выберите марку')]),
            'description': forms.Textarea(attrs={'rows': 5}),
            'tags': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self._init_bootstrap()
        self.fields['brand'].widget.attrs['data-models'] = '1'
        self.fields['model'].widget.attrs['data-current-model'] = self.initial.get('model', '') or getattr(self.instance, 'model', '')

        selected_brand = self.data.get('brand') or self.initial.get('brand') or getattr(self.instance, 'brand', '')
        model_choices = [('', 'Выберите модель')]
        if selected_brand in self.CAR_MODELS:
            model_choices += [(model, model) for model in self.CAR_MODELS[selected_brand]]
        self.fields['model'].widget.choices = model_choices
        self.fields['car_image'].required = not (self.instance.pk and self.instance.images.exists())
        if self.fields['car_image'].required:
            self.fields['car_image'].help_text = 'Загрузите фото, чтобы объявление не отображалось без изображения.'

        if self.user and self.user.is_authenticated and not self.initial:
            profile = getattr(self.user, 'profile', None)
            full_name = [self.user.last_name, self.user.first_name]
            if profile:
                self.fields['seller_phone'].initial = profile.phone
                self.fields['seller_city'].initial = profile.city
            self.fields['seller_email'].initial = self.user.email
            self.fields['seller_last_name'].initial = self.user.last_name
            self.fields['seller_first_name'].initial = self.user.first_name

    def clean_seller_phone(self):
        phone = self.cleaned_data['seller_phone'].strip()
        if not PHONE_REGEXP.match(phone):
            raise forms.ValidationError('Телефон не соответствует формату.')
        return phone

    def clean(self):
        cleaned = super().clean()
        min_year = 1980
        max_year = 2030
        year = cleaned.get('year')
        price = cleaned.get('price')
        mileage = cleaned.get('mileage')
        if year and not (min_year <= year <= max_year):
            self.add_error('year', f'Год должен быть от {min_year} до {max_year}.')
        if price is not None and price <= 0:
            self.add_error('price', 'Цена должна быть больше 0.')
        if mileage is not None and mileage < 0:
            self.add_error('mileage', 'Пробег не может быть отрицательным.')
        return cleaned


class MessageForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Message
        fields = ['buyer_name', 'buyer_email', 'text']
        widgets = {'text': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['buyer_name'].initial = user.get_full_name() or user.username
            self.fields['buyer_email'].initial = user.email
        self._init_bootstrap()


class ReviewForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {'comment': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_bootstrap()
