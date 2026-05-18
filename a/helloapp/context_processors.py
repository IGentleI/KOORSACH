def user_roles(request):
    user = request.user
    if not user.is_authenticated:
        return {'is_buyer': False, 'is_seller': False, 'is_moderator': False}
    return {
        'is_buyer': user.groups.filter(name='Buyer').exists(),
        'is_seller': user.groups.filter(name='Seller').exists(),
        'is_moderator': user.groups.filter(name='Moderator').exists() or user.is_staff,
    }
