                                       #THIS ALL GONNA SHOW UP IN ADMIN PAGE.

                                       
from django.db.models.signals import post_save
from django.conf import settings #bcz auth is in settings.
from django.db import models
from django.shortcuts import reverse
#from django_countries.fields import CountryField



# Create your models here.

CATEGORY_CHOICES=(('S', 'Shirt'),
				  ('SW', 'Sportswear'),
				  ('OW', 'Outwear'),
				  ('MP', 'Cell Phone'),
				  ('TV', 'Television'),
				  ('EC', 'Electronics'))

LABEL_CHOICES = (('P', 'primary'),
				 ('S', 'secondary'),
				 ('D', 'danger'))

ADDRESS_CHOICES = (('B', 'Billing'),
					('S', 'Shipping'))

# WE created two things CATEGORY_CHOICES and LABEL_CHOICES inside Item section to display it on admin-page

class UserProfile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)
	stripe_customer_id = models.CharField(max_length = 50, blank=True, null=True)
	one_click_purchasing = models.BooleanField(default=False)

	def __str__(self):
		return self.user.username



class Item(models.Model):  # This is displayed at list of items.
	title = models.CharField(max_length=100)
	price = models.FloatField()
	discount_price = models.FloatField(blank=True, null=True)
	category = models.CharField(choices = CATEGORY_CHOICES, max_length=2)
	label = models.CharField(choices = LABEL_CHOICES, max_length=1)
	description = models.TextField()
	slug = models.SlugField()
	image = models.ImageField()


	def __str__(self):
		return self.title
    
    #  These are REVERSE function!

	def get_absolute_url(self):
		return reverse("core:product", kwargs={'slug':self.slug})
			
	def get_add_to_cart_url(self):
		return reverse("core:add_to_cart", kwargs={'slug':self.slug})

	def get_remove_from_cart_url(self):
		return reverse("core:remove_from_cart", kwargs={'slug':self.slug})




class OrderItem(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	ordered = models.BooleanField(default = False)
	item = models.ForeignKey(Item, on_delete=models.CASCADE) #Linking item with Item
	quantity = models.IntegerField(default=1) #when we call add_to_cart function then for adding item we need quantity field.

	def __str__(self):
		return f"{self.quantity} of {self.item.title}"

	def get_total_item_price(self):
		return self.quantity * self.item.price

	def get_total_discount_item_price(self):
		return self.quantity * self.item.discount_price

	def get_amount_saved(self):
		return self.get_total_item_price() - self.get_total_discount_item_price()

	def get_final_price(self):
		if self.item.discount_price:
			return self.get_total_discount_item_price()
		return self.get_total_item_price()



class Order(models.Model):  # You can basically view this as Cart.
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) #Just taking user
	ref_code = models.CharField(max_length=20, blank=True, null = True) #reference code for tracking order.
	items = models.ManyToManyField(OrderItem)  #Adding OderItems into Order.
	start_date = models.DateTimeField(auto_now_add=True)
	ordered_date = models.DateTimeField()
	ordered = models.BooleanField(default = False)
	#This Field for referencing the Payment
	payment = models.ForeignKey('Payment', on_delete = models.SET_NULL, blank=True, null = True)
	#This Field for referencing the Shipping_Address
	shipping_address = models.ForeignKey('Address', related_name= 'shipping_address', on_delete = models.SET_NULL, blank=True, null = True)
	#This Field for referencing the Billing_Address
	billing_address = models.ForeignKey('Address', related_name='billing_address', on_delete = models.SET_NULL, blank=True, null = True) 
	#This Field for referencing the Coupn.
	coupon = models.ForeignKey('Coupon', on_delete = models.SET_NULL, blank=True, null=True)

	#These fields keep track of order
	being_delivered = models.BooleanField(default=False)
	recieved = models.BooleanField(default=False)
	refund_requested = models.BooleanField(default=False)
	refund_granted = models.BooleanField(default=False)

	'''
	1. Item Added to cart
	2. Adding a billing address
	 (failed checkout due to not having valid stripe keys.)
	3. Payment
	 (preprocessing, processing, packaging etc)
	4. Being delivered
	5. Recieved
	6. Refunds
	'''

	def __str__(self):
		return self.user.username

	def get_total(self):
		total=0
		for order_item in self.items.all(): #Looping through all the items
			total += order_item.get_final_price()
		if self.coupon:
			total -= self.coupon.amount #when we apply coupon it gonna subtract amount in coupon.
		return total

def __str__(self):
	return self.title

class Address(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) #Just taking user
	street_address = models.CharField(max_length=100)
	apartment_address = models.CharField(max_length=100)
	#country = CountryField(multiple = False)
	zip = models.CharField(max_length=100)
	address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
	default = models.BooleanField(default = False)

	def __str__(self):
		return self.user.username

	class Meta:
		verbose_name_plural = 'Addresses'


#Keeping track of Stripe payment
class Payment(models.Model):
	stripe_charge_id = models.CharField(max_length=50)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
	#on_delete.SET_NULL this is when we delete user payment don't got deleted.
	amount = models.FloatField()
	timestamp = models.DateTimeField(auto_now_add = True)

	def __str__(self):
		return self.user.username

class Coupon(models.Model):
	code = models.CharField(max_length=15)
	amount = models.FloatField()

	def __str__(self):
		return self.code

class Refund(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE)
	reason = models.TextField()
	accepted = models.BooleanField(default=False)
	email = models.EmailField()

	def __str__(self):
		return f"{self.pk}" #we returned like this bcz it's an id not a string.


def userprofile_reciever(sender, instance, created, *args, **kwargs):
	if created:
		userprofile = UserProfile.objects.create(user=instance)

post_save.connect(userprofile_reciever, sender = settings.AUTH_USER_MODEL)