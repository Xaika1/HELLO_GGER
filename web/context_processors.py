def cart_count(request):
    if not request.user.is_authenticated:
        return {'cart_count': 0}
    return {'cart_count': sum(request.user.cart.values_list('quantity', flat=True))}
