from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm
from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund, UserProfile
from django.shortcuts import redirect
from django.utils import timezone

import random
import string
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.

#creating function for reference code.
def create_ref_code():
	return ''.join(random.choices(string.ascii_lowercase + string.digits, k = 20))


#Checking for someone is passing empty string.
def is_valid_form(values):
	valid = True
	for field in values:
		if field=='':
			valid=False
	return valid



# Check Out View
class CheckoutView(View):
	#defining get request
	def get(self, *args, **kwargs):
		#from
		try:
			order = Order.objects.get(user=self.request.user, ordered=False)
			form = CheckoutForm()
			context = {
				'form':form,
				'couponform':CouponForm(),
				'order':order,
				'DISPLAY_COUPON_FORM': True
				}

			shipping_address_qs = Address.objects.filter(
				user=self.request.user,
				address_type = 'S',
				default = True
				)
			if shipping_address_qs.exists(): #Updating context setting 1st address as default
				context.update({'default_shipping_address':shipping_address_qs[0]})

			billing_address_qs = Address.objects.filter(
				user=self.request.user,
				address_type = 'B',
				default = True
				)
			if billing_address_qs.exists(): #Updating context setting 1st address as default
				context.update({'default_billing_address':billing_address_qs[0]})			



			return render(self.request, 'checkout.html', context)
		except ObjectDoesNotExist:
			messages.info(self.request, "You do not have an active order!")
			return redirect("core:checkout")

	            						#post method is used when we submit something
	
	#this function is for when we click 
	def post(self, *args, **kwargs):
		#in this we will get post request of that checkout form so we need to import it.
		form = CheckoutForm(self.request.POST or None) 
		#print(self.request.POST)
		try:
			order = Order.objects.get(user = self.request.user, ordered = False) #checking if order is available or not.
			if form.is_valid(): #checking for all necessary fields in form.

												# This is for SHIPPING.

				use_default_shipping = form.cleaned_data.get('use_default_shipping')
				if use_default_shipping:
					print("Using the default shipping address")
					address_qs = Address.objects.filter(
						user=self.request.user,
						address_type='S',
						default = True
						)

					if address_qs.exists():
						shipping_address = address_qs[0]
						order.shipping_address = shipping_address
						order.save()

					else:
						messages.info(self.request, "No default shipping address available")
						return redirect('core:checkout')

				else:
					print("User is entering a new shipping address")

					shipping_address1 = form.cleaned_data.get('shipping_address') #Getting info inside shipping_address
					shipping_address2 = form.cleaned_data.get('shipping_address2') #Getting info inside shipping_address2
					#country = form.cleaned_data.get('country')
					shipping_zip = form.cleaned_data.get('shipping_zip') #Getting info inside shipping_zip
					
					if is_valid_form([shipping_address1, shipping_zip]):

						shipping_address = Address(
							user = self.request.user,
							street_address = shipping_address1,
							apartment_address = shipping_address2,
							#country = country,
							zip = shipping_zip,
							address_type = 'S'
							)

						shipping_address.save()

						order.shipping_address = shipping_address
						order.save()

						set_default_shipping = form.cleaned_data.get('set_default_shipping')
						if set_default_shipping:
							shipping_address.default = True
							shipping_address.save()

					else:
						messages.info(self.request, "Please fill the required address fields")
				
											# This is for BILLING.

				use_default_billing = form.cleaned_data.get('use_default_billing')
				same_billing_address = form.cleaned_data.get('same_billing_address')

				if same_billing_address:
					billing_address = shipping_address
					billing_address.pk = None #cloning it
					billing_address.save()
					billing_address.address_type = 'B'
					billing_address.save()
					order.billing_address = billing_address
					order.save()



				elif use_default_billing:
					print("Using the default billing address")
					address_qs = Address.objects.filter(
						user=self.request.user,
						address_type='B',
						default = True
						)

					if address_qs.exists():
						billing_address = address_qs[0]
						order.billing_address = billing_address
						order.save()

					else:
						messages.info(self.request, "No default billing address available")
						return redirect('core:checkout')

				else:
					print("User is entering a new billing address")

					billing_address1 = form.cleaned_data.get('billing_address') #Getting info inside billing_address
					billing_address2 = form.cleaned_data.get('billing_address2') #Getting info inside billing_address2
					#country = form.cleaned_data.get('country')
					billing_zip = form.cleaned_data.get('billing_zip') #Getting info inside billing_zip
					
					if is_valid_form([billing_address1, billing_zip]):

						billing_address = Address(
							user = self.request.user,
							street_address = billing_address1,
							apartment_address = billing_address2,
							#country = country,
							zip = billing_zip,
							address_type = 'B'
							)

						billing_address.save()

						order.billing_address = billing_address
						order.save()

						set_default_billing = form.cleaned_data.get('set_default_billing')
						if set_default_billing:
							billing_address.default = True
							billing_address.save()

					else:
						messages.info(self.request, "Please fill the required address fields")




				payment_option = form.cleaned_data.get('payment_option') #Getting info inside payment_option
				#TODO: add a redirect to selected payments option
				if payment_option == 'S':
					return redirect('core:payment', payment_option = 'stripe')
				elif payment_option == 'P':
					return redirect('core:payment', payment_option = 'paypal')
				else:
					message.warning(self.request, "Invalid payment option selected")
					return render('core:checkout')


		except ObjectDoesNotExist:
			messages.warning(self.request, "You do not have an active order")
			return redirect("core:order_summary")


		
			#print(form.cleaned_data) #means printing all info inside form in cmd.
			#print('The form is valid!') #Printing The form is valid! in cmd. 
			

#PAYMENT VIEW
class PaymentView(View):
	def get(self, *args, **kwargs):
		#order
		order = Order.objects.get(user = self.request.user, ordered = False)
		if order.billing_address:
			context = {
				'order':order,
				'DISPLAY_COUPON_FORM': False,
				'STRIPE_PUBLIC_KEY' : settings.STRIPE_PUBLIC_KEY
			} 

			userprofile = self.request.user.userprofile
			if userprofile.one_click_purchasing:
				#fetch the users card list
				cards = stripe.Customer.list_sources(
					userprofile.stripe_customer_id,
					limit = 3,
					object = 'card'
					)
				card_list = cards['data']
				if len(card_list)>0:
					#update the context with default card
					context.update({
						'card':card_list[0]
						})
			return render(self.request, 'payment.html', context)
		else:
			messages.warning(self.request, "You do not have a billing address")
			return redirect("core:checkout")

	#this function is for when we submit payment
	def post(self, *args, **kwargs):
		order = Order.objects.get(user = self.request.user, ordered = False)
		form = PaymentForm(self.request.POST)
		userprofile = UserProfile.objects.get(user = self.request.user)
		if form.is_valid():
			token = form.cleaned_data.get('stripeToken')
			save = form.cleaned_data.get('save')
			use_default = form.cleaned_data.get('use_default')

			if save:
				#allow to fetch cards
				if not userprofile.stripe_customer_id:
					customer = stripe.Customer.create(
						email = self.request.user.email,
						source=token
						)
					userprofile.stripe_customer_id = customer['id']
					userprofile.one_click_purchasing = True
					userprofile.save()
				else:
					stripe.Customer.create_source(
						userprofile.stripe_customer_id,
						source=token
						)


		#token = self.request.POST.get('stripeToken') #getting token from request.
		amount = int(order.get_total() * 100)#amount will be the amount of current order. in 2nd line taking order

		try:

			if use_default:
				#if we use default card.
				charge = stripe.Charge.create(
					amount = amount, #in cents
					currency = 'usd',
					customer = userprofile.stripe_customer_id
					)

			else:
				charge = stripe.Charge.create(
					amount = amount, #in cents
					currency = 'usd',
					source=token
					)

			#create payment
			payment = Payment()
			payment.stripe_charge_id = charge['id']
			payment.user = self.request.user
			payment.amount = order.get_total()
			payment.save()

			#After this we save the payment details mentioned above to database
			#when we order or delete item it must start with quantity one thats the code for this.
			order_items = order.items.all()
			order_items.update(ordered=True)
			for item in order_items:
				item.save()

			#Assigning the payment to the order.
			#After this when we click submit payment the order is ordered so we are going to change ordered to True for this item.
			order.ordered = True 
			order.payment = payment
			order.ref_code = create_ref_code() #creating reference code.
			order.save()

			#Redirecting to some confirmation page
			messages.success(self.request, "Your order was successful!")
			return redirect("/")

		except stripe.error.CardError as e:
			body = e.json_body
			err = body.get('error', {})
			messages.warning(self.request, f"{err.get('message')}")
			return redirect("/")

		except stripe.error.RateLimitError as e:
			# Too many request are made to the API too quickly
			messages.warning(self.request, "Rate Limit Error")
			return redirect("/")

		except stripe.error.InvalidRequestError as e:
			# Invalid Parameters were supplied to Stripe's API
			messages.warning(self.request, "Invalid Parameters")
			return redirect("/")

		except stripe.error.AuthenticationError as e:
			# Authentication with stripe API failed
			#(maybe you changed API's keys recently)
			messages.warning(self.request, "Not Authenticated")
			return redirect("/")

		except stripe.error.APIConnectionError as e:
			# Network communication with stripe failed
			messages.warning(self.request, "Network Error")
			return redirect("/")

		except stripe.error.StripeError as e:
			# Dispaly a very generic error to the user
			# and maybe send yourself an email
			messages.warning(self.request, "something went wrong, you were not charged, please try again!")
			return redirect("/")

		except Exception as e:
			# send an email to yourself
			messages.warning(self.request, "A serious error occured. We have been notified.")
			return redirect("/")



#Home View
class HomeView(ListView):
    model = Item
    paginate_by = 8
    template_name = 'home.html'

# CART
class OrderSummaryView(LoginRequiredMixin, View):
	def get(self, *args, **kwargs):
		try:
			order = Order.objects.get(user = self.request.user, ordered = False)
			context = {'object':order}
			return render(self.request, 'order_summary.html', context)
		except ObjectDoesNotExist:
			messages.error(self.request, "You do not have an active order")
			return redirect("/")
		

#Class for showing product in detail and also add_to_cart, remove_from_cart functions and remove_single_item_from_cart
class ItemDetailView(DetailView):
	model = Item
	template_name = 'product.html'
	
#Adding single item to cart.
@login_required
def add_to_cart(request, slug):
	item = get_object_or_404(Item, slug=slug) #getting item
	order_item, created = OrderItem.objects.get_or_create(item=item, user =request.user, ordered = False) #Creating objects  #it's user from Order class in models.py
	order_qs = Order.objects.filter(user=request.user, ordered = False) 
	#ordered make sure that we are not getting duplicate object.
	if order_qs.exists():
		order = order_qs[0]
		# check if the order item is in the order
		if order.items.filter(item__slug=item.slug).exists():
			order_item.quantity += 1
			order_item.save()
			messages.info(request, "This Item quantity is updated!")
			return redirect('core:order_summary')
		else:
			messages.info(request, "This Item was added to your cart!")
			order.items.add(order_item)
			return redirect('core:order_summary')

	else:
		ordered_date = timezone.now()
		order = Order.objects.create(user=request.user, ordered_date=ordered_date)
		order.items.add(order_item)
		messages.info(request, "This Item was added to your cart!")
		return redirect('core:order_summary')
	

#Removing the whole order from cart.
@login_required
def remove_from_cart(request, slug):
	item = get_object_or_404(Item, slug=slug) # getting item
	order_qs = Order.objects.filter(user = request.user, ordered = False)

	#checking if order exists.
	if order_qs.exists():
		order = order_qs[0] #Grabbing the item
		#check if the order item is in order
		if order.items.filter(item__slug=item.slug).exists():
			order_item = OrderItem.objects.filter(item = item, user = request.user, ordered = False)[0]
			order.items.remove(order_item)
			messages.info(request, "This Item was removed from your cart!")
			return redirect('core:order_summary') #removing slug bcz we provided inside order_summary.html

		else:
			#add a message saying the order doesn't contain the item
			messages.info(request, "This Item was not in your cart!")
			return redirect('core:product', slug=slug)
	else:
		#add amessage saying user doesn't have an order
		messages.info(request, "you do not have an active order!")
		return redirect('core:product', slug=slug)


#This if for removing a single item as mainly from cart by minus button
@login_required
def remove_single_item_from_cart(request, slug):
	item = get_object_or_404(Item, slug=slug) # getting item or display 404 error.
	order_qs = Order.objects.filter(user = request.user, ordered = False)

	#checking if order exists.
	if order_qs.exists():
		order = order_qs[0] #Grabbing the item
		#check if the order item is in order
		if order.items.filter(item__slug=item.slug).exists():
			order_item = OrderItem.objects.filter(item = item, user = request.user, ordered = False)[0]
			if order_item.quantity > 1:
				order_item.quantity -= 1
				order_item.save()
			else:
				order.items.remove(order_item)
			
			messages.info(request, "This Item quantity is updated!")
			return redirect('core:order_summary') #we don't need to pass a slug here

		else:
			#add a message saying the order doesn't contain the item
			messages.info(request, "This Item was not in your cart!")
			return redirect('core:product', slug=slug)
	else:
		#add amessage saying user doesn't have an order
		messages.info(request, "you do not have an active order!")
		return redirect('core:product', slug=slug)


#For checking if coupon exists or not. if exists then getting the coupon.
def get_coupon(request, code):
	try:
		coupon = Coupon.objects.get(code=code)
		return coupon

	except ObjectDoesNotExist:
		messages.info(request, "This Coupon doesn't exist!")
		return redirect('core:checkout')

#for adding coupon. Changing add_coupon to class based view
class AddCouponView(View):
	def post(self, *args, **kwargs):
		form = CouponForm(self.request.POST or None)
		if form.is_valid():
			try:
				code = form.cleaned_data.get('code') #Getting info inside code section.
				order = Order.objects.get(user=self.request.user, ordered=False)
				order.coupon = get_coupon(self.request, code) #Assigning coupon to order.
				order.save()
				messages.success(self.request, "Coupon Applied!")
				return redirect('core:checkout')

			except ObjectDoesNotExist:
				messages.info(request, "You do not have an active order!")
				return redirect("core:checkout")

class RefundRequestView(View):
	def get(self, *args, **kwargs):
		form = RefundForm()
		context={
			    'form':form
		 	    }
		return render(self.request, "request_refund.html", context)
 

	def post(self, *args, **kwargs):
		form = RefundForm(self.request.POST)
		if form.is_valid():
			ref_code = form.cleaned_data.get('ref_code')
			message = form.cleaned_data.get('message')
			email = form.cleaned_data.get('email')

			#edit the order
			try:
				order = Order.objects.get(ref_code=ref_code)
				order.refund_requested = True
				order.save()

				#store the Refund
				refund = Refund()
				refund.order = order
				refund.reason = message
				refund.email = email
				refund.save()

				messages.info(self.request, "Your request was recieved.")
				return redirect("core:request_refund")

			except ObjectDoesNotExist:
				messages.info(self.request, "This order doesn't exist.")
				return redirect("core:request_refund")