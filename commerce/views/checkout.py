from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail.message import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from django.shortcuts import redirect
from django.template import loader
from django.template.context import Context
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View, TemplateResponseMixin
from django.views.generic.edit import FormView
from commerce.app_settings import COMMERCE_THUMBNAIL_SIZE, COMMERCE_EMAIL_FROM

from commerce.forms.account import LoginForm, RegistrationForm, \
    CheckoutProfileForm
from commerce.forms.checkout import ShippingPaymentForm
from commerce.models.account import Profile
from commerce.models.order import Line, Information
from commerce.utils.cart import get_cart
from fitt.settings import COMMERCE_URL


SHIPPING_PAYMENT_IDENTIFIER = 'shipping_payment'


class LoginRegisterView(TemplateResponseMixin, View):
    template_name = 'commerce/checkout/login-register.html'

    def dispatch(self, request, *args, **kwargs):
        cart = get_cart(request)
        if cart.is_empty():
            messages.error(
                request,
                _(u'You can not access this page when your cart is empty.'))
            return redirect('home')

        if request.user.is_authenticated():
            return redirect('commerce_checkout_profile')

        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Shopping cart'),
             'url': reverse('commerce_cart')},
            {'name': _(u'Checkout'),
             'url': reverse('commerce_checkout_login_register')},
            {'name': _(u'Login or register'),
             'url': reverse('commerce_checkout_login_register')})
        return super(LoginRegisterView, self).dispatch(
            request, *args, **kwargs)

    def _login(self, username, password):
        user = authenticate(username=username, password=password)
        if user is None:
            messages.error(
                self.request,
                _(u'Your username or password was incorrect.'))
            return False
        elif user.is_active is True:
            login(self.request, user)
            messages.success(self.request, _(u'Login was successful.'))
            return True
        else:
            messages.error(self.request, _(u'Your account is not active.'))
            return False

    def _registration(self, username, password):
        user = User.objects.create_user(
            username=username, email=username, password=password)
        user.save()
        messages.success(self.request, _(u'Registration was successful.'))
        return user

    def get(self, request):
        return self.render_to_response({
            'login_form': LoginForm(),
            'registration_form': RegistrationForm(),
        })

    def post(self, request):
        login_form = LoginForm()
        registration_form = RegistrationForm()

        if 'login' in request.POST:
            login_form = LoginForm(request.POST)

            if login_form.is_valid():
                data = login_form.cleaned_data
                login_state = self._login(
                    data.get('username'), data.get('password'))

                if login_state is True:
                    return redirect('commerce_checkout_profile')
        elif 'registration' in request.POST:
            registration_form = RegistrationForm(request.POST)

            if registration_form.is_valid():
                data = registration_form.cleaned_data
                self._registration(data.get('username'), data.get('password'))
                self._login(data.get('username'), data.get('password'))
                return redirect('commerce_checkout_profile')

        return self.render_to_response({
            'login_form': login_form,
            'registration_form': registration_form,
        })


class ProfileView(FormView):
    form_class = CheckoutProfileForm
    template_name = 'commerce/checkout/profile.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        cart = get_cart(request)
        if cart.is_empty():
            messages.error(
                request,
                _(u'You can not access this page when your cart is empty.'))
            return redirect('home')

        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Shopping cart'),
             'url': reverse('commerce_cart')},
            {'name': _(u'Checkout'),
             'url': reverse('commerce_checkout_login_register')},
            {'name': _(u'Profile information'),
             'url': reverse('commerce_checkout_profile')})
        return super(ProfileView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('commerce_checkout_shipping_payment')

    def get_form(self, form_class):
        try:
            user = self.request.user
            profile = Profile.objects.get(user=user)
            return form_class(
                self.request.POST or None,
                instance=profile,
                initial={
                    'first_name': user.first_name, 'last_name': user.last_name}
            )
        except ObjectDoesNotExist:
            return form_class(self.request.POST or None)

    def form_valid(self, form):
        data = form.cleaned_data
        user = self.request.user

        # User
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.save()

        # Profile
        profile = form.save(commit=False)
        profile.user = user
        profile.save()

        messages.success(self.request, _(u'Profile successfully saved.'))
        return super(ProfileView, self).form_valid(form)


class ShippingPaymentView(FormView):
    form_class = ShippingPaymentForm
    template_name = 'commerce/checkout/shipping-payment.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        # Cart not empty
        cart = get_cart(request)
        if cart.is_empty():
            messages.error(
                request,
                _(u'You can not access this page when your cart is empty.'))
            return redirect('home')

        # Profile information not filled
        try:
            Profile.objects.get(user=request.user)
        except ObjectDoesNotExist:
            messages.error(request, _(u'Profile information missing.'))
            return redirect('commerce_checkout_profile')

        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Shopping cart'), 'url': reverse('commerce_cart')},
            {'name': _(u'Checkout'),
             'url': reverse('commerce_checkout_login_register')},
            {'name': _(u'Shipping and payment'),
             'url': reverse('commerce_checkout_shipping_payment')})
        return super(ShippingPaymentView, self).dispatch(
            request, *args, **kwargs)

    def get_success_url(self):
        return reverse('commerce_checkout_confirm')

    def form_valid(self, form):
        self.request.session[SHIPPING_PAYMENT_IDENTIFIER] = form.cleaned_data
        return super(ShippingPaymentView, self).form_valid(form)


class ConfirmView(View, TemplateResponseMixin):
    template_name = 'commerce/checkout/confirm.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        # Cart not empty
        cart = get_cart(request)
        if cart.is_empty():
            messages.error(
                request,
                _(u'You can not access this page when your cart is empty.'))
            return redirect('home')

        # Profile information not filled
        try:
            self.profile = Profile.objects.get(user=request.user)
        except ObjectDoesNotExist:
            messages.error(request, _(u'Profile information missing.'))
            return redirect('commerce_checkout_profile')

        # Shipping payment filled
        if SHIPPING_PAYMENT_IDENTIFIER not in request.session:
            messages.error(
                request, _(u'Shipping or payment information missing.'))
            return redirect('commerce_checkout_shipping_payment')

        initial = request.session.get(SHIPPING_PAYMENT_IDENTIFIER, None)

        self.shipping_payment_form = ShippingPaymentForm(
            initial, initial=initial, request=request)

        if not self.shipping_payment_form.is_valid():
            raise Exception()

        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Shopping cart'), 'url': reverse('commerce_cart')},
            {'name': _(u'Checkout'),
             'url': reverse('commerce_checkout_login_register')},
            {'name': _(u'Order confirmation'),
             'url': reverse('commerce_checkout_confirm')})
        return super(ConfirmView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        cart = get_cart(request)
        return self.render_to_response({
            'profile': self.profile,
            'cart': cart,
            'total': cart.total() + self.shipping_payment_form.price(),
            'shipping_payment_form': self.shipping_payment_form,
        })

    def post(self, request):
        cart = get_cart(request)

        # Create order
        order = self.shipping_payment_form.save(commit=False)
        order.user = request.user
        order.price_shipping = self.shipping_payment_form.price()
        order.total = cart.total() + self.shipping_payment_form.price()
        order.save()

        # Assign products to order
        for item in cart.items:
            Line.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                total=item.price(),
                price=item.product.price,
                price_discount=item.product.price_discount,
            )

        # Save profile information
        information_dict = self._prepare_information()
        information_dict['order_id'] = order.id
        information = Information(**information_dict)
        information.save()

        t = loader.get_template('commerce/mails/order-created.html')
        c = Context({
            'order': order,
            'host': COMMERCE_URL,
            'size': COMMERCE_THUMBNAIL_SIZE,
        })

        message = EmailMultiAlternatives(
            _(u'New order created'), '',
            COMMERCE_EMAIL_FROM, [order.user.email])
        message.attach_alternative(t.render(c), 'text/html')
        message.send()

        t = loader.get_template('commerce/mails/order-inform-admin.html')
        c = Context({
            'order': order,
            'host': COMMERCE_URL,
            'size': COMMERCE_THUMBNAIL_SIZE,
        })

        message = EmailMultiAlternatives(
            _(u'New order created'), '',
            COMMERCE_EMAIL_FROM, settings.EDITORS)
        message.attach_alternative(t.render(c), 'text/html')
        message.send()

        # Flush sessions
        if SHIPPING_PAYMENT_IDENTIFIER in request.session:
            del request.session[SHIPPING_PAYMENT_IDENTIFIER]
        cart.clean()

        messages.success(request, _(u'Order was successful.'))
        return redirect('home')

    def _prepare_information(self):
        profile_dict = model_to_dict(self.profile)
        del profile_dict['id']
        del profile_dict['user']
        del profile_dict['is_newsletter']
        del profile_dict['created']
        del profile_dict['modified']
        return profile_dict
