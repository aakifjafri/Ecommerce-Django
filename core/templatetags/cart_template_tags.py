from django import template
from core.models import Order

register = template.Library() #For registering our template

@register.filter
def cart_item_count(user):
	if user.is_authenticated:
		qs = Order.objects.filter(user = user, ordered = False)  #user is from models/Order
		if qs.exists():
			return qs[0].items.count() # returning the count we've done in Views/add_to_cart by addition
	return 0