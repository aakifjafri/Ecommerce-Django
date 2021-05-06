from django import forms
#from django_countries.fields import CountryField  # after installing django_countries
#from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICES = (
	('S','Stripe'),
	('P','PayPal')
	)

#For saving info about all info that you provided.
class CheckoutForm(forms.Form):
	shipping_address = forms.CharField(required = False)
	shipping_address2 = forms.CharField(required = False) # we put required = False bcz its optional

	"""country = CountryField(blank_label='(select country)').formfield(widget = CountrySelectWidget(attrs={
					'class':'custom-select d-block w-100'
					}))"""
	shipping_zip = forms.CharField(required=False)
	same_billing_address = forms.BooleanField(required = False)
	set_default_shipping = forms.BooleanField(required = False)
	use_default_shipping = forms.BooleanField(required = False)
	
	billing_address = forms.CharField(required=False)
	billing_address2 = forms.CharField(required=False)
	billing_zip = forms.CharField(required=False)
	
	set_default_billing = forms.BooleanField(required=False)
	use_default_billing = forms.BooleanField(required=False)	



	payment_option = forms.ChoiceField(
		widget = forms.RadioSelect, choices = PAYMENT_CHOICES) #RadioSelect is used so that we can only select one at a time.
	

#For saving info about which coupon is applied to which product
class CouponForm(forms.Form):
	code = forms.CharField(widget=forms.TextInput(attrs={
		'class':'form-control',
		'placeholder':'Promo code',
		'aria-label':'Recipient\'s username',
		'aria-describedby':'basic-addon2'
		}))


class RefundForm(forms.Form):
	ref_code = forms.CharField()
	message = forms.CharField(widget=forms.Textarea(attrs={'rows':4}))
	email = forms.EmailField()

class PaymentForm(forms.Form):
    stripeToken = forms.CharField(required=False)
    save = forms.BooleanField(required=False)
    use_default = forms.BooleanField(required=False)