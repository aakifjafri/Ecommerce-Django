from django.contrib import admin

# Register your models here.
from .models import Item, OrderItem, Order, Payment, Coupon, Refund, Address, UserProfile

#making refund_requested=False and refund_granted=True
def make_refund_accepted(Modeladmin, request, queryset):
	queryset.update(refund_requested=False, refund_granted=True)

make_refund_accepted.short_description = "Update orders to refund granted"


def make_delievered(Modeladmin, request, queryset):
	queryset.update(being_delivered=True)

make_delievered.short_description = "Update orders to being delivered"


def make_recieved(Modeladmin, request, queryset):
	queryset.update(recieved=True)

make_recieved.short_description = "Update orders to recieved"

class OrderAdmin(admin.ModelAdmin):#This class is for displaying ordered, and manages refunds by telling us yes or no in Orders/admin.
	list_display = ['user',
	 				'ordered',
					'being_delivered',
					'recieved',
					'refund_requested',
					'refund_granted',
					'shipping_address',
					'billing_address',
					'payment',
					'coupon'
					]

	#Links to go to these fields.
	list_display_links = ['user', 
						  'shipping_address',
						  'billing_address',
						  'payment',
						  'coupon'
						 ]

	#This displays in Orders/admin
	list_filter = ['ordered',
					'being_delivered',
					'recieved',
					'refund_requested',
					'refund_granted'
					]

	search_fields = [ 'user__username', 'ref_code']

	actions = [make_refund_accepted, make_delievered, make_recieved]


class AddressAdmin(admin.ModelAdmin):
	list_display = ['user',
					'street_address',
					'apartment_address',
					'zip',
					'address_type',
					'default'
					]

	list_filter = ['default',
				   'address_type'
				   ]

	search_fields = ['user', 'street_address', 'apartment_address', 'zip']


admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Refund)
admin.site.register(Address, AddressAdmin)
admin.site.register(UserProfile)