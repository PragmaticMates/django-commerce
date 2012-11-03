from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.mail.message import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.template import loader, Context
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View
from django.views.generic.edit import FormView

from commerce.app_settings import COMMERCE_EMAIL_FROM
from commerce.forms.account import LoginForm, PasswordForm, RegistrationForm, \
    ProfileForm, RecoverForm
from commerce.models.account import Profile
from fitt.settings import COMMERCE_URL


class RegistrationView(FormView):
    template_name = 'commerce/accounts/registration.html'
    form_class = RegistrationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            messages.error(
                request,
                _(u'You can not access this page when you are logged in.'))
            return redirect(reverse('home'))

        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Registration'),
             'url': reverse('commerce_accounts_registration')})
        return super(RegistrationView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.cleaned_data

        # Registration
        try:
            user = User.objects.create_user(
                username=data.get('username'),
                email=data.get('username'),
                password=data.get('password'),
            )
            user.save()
        except Exception:
            messages.error(
                self.request, _(u'There was an error in registration.'))
            return redirect('commerce_accounts_registration')

        # Login
        user = authenticate(
            username=data.get('username'),
            password=form.data.get('password'))
        if user is None:
            messages.error(
                self.request, _(u'Your username or password was incorrect.'))
            return redirect(reverse('commerce_accounts_registration'))
        elif user.is_active is True:
            login(self.request, user)
            messages.success(self.request, _(u'Registration was successfull.'))
            return redirect('commerce_accounts_profile')
        else:
            messages.error(self.request, _(u'Your account is not active.'))

        return super(RegistrationView, self).form_valid(form)

    def get_success_url(self):
        return reverse('home')


class ProfileView(FormView):
    template_name = 'commerce/accounts/profile.html'
    form_class = ProfileForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Profile'),
             'url': reverse('commerce_accounts_profile')})
        return super(ProfileView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('commerce_accounts_profile')

    def get_form(self, form_class):
        try:
            profile = Profile.objects.get(user=self.request.user)
            return form_class(
                self.request.POST or None,
                instance=profile,
                initial={
                    'first_name': profile.user.first_name,
                    'last_name': profile.user.last_name}
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


class LoginView(FormView):
    template_name = 'commerce/accounts/login.html'
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        self.next_page = request.GET.get('next', None)

        if request.user.is_authenticated():
            messages.error(request, _(u'You are already logged in!'))
            return redirect(reverse('home'))

        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Recover password'),
             'url': reverse('commerce_accounts_login')})
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'])
        if user is None:
            messages.error(
                self.request, _(u'Your username or password was incorrect.'))
            return redirect(reverse('commerce_accounts_login'))
        elif user.is_active is True:
            login(self.request, user)
        else:
            messages.error(self.request, _(u'Your account is not active!'))

        return super(LoginView, self).form_valid(form)

    def get_success_url(self):
        if self.next_page is None:
            return reverse('home')
        return self.next_page


class RecoverView(FormView):
    template_name = 'commerce/accounts/recover.html'
    form_class = RecoverForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseForbidden()

        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Recover'),
             'url': reverse('commerce_accounts_recover')})
        return super(RecoverView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('home')

    def form_valid(self, form):
        data = form.cleaned_data
        email = data['email']

        try:
            user = User.objects.get(email=email)
            password = User.objects.make_random_password()
            user.set_password(password)
            user.save()

            t = loader.get_template('commerce/mails/recover-password.html')
            c = Context({
                'host': COMMERCE_URL,
                'password': password,
            })

            message = EmailMultiAlternatives(
                _(u'Password recover'), '', COMMERCE_EMAIL_FROM, [user.email])
            message.attach_alternative(t.render(c), 'text/html')
            message.send()
        except ObjectDoesNotExist:
            pass

        messages.success(
            self.request,
            _(u'New password was successfully sent on your email.'))
        return super(RecoverView, self).form_valid(form)


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, _(u'You have been successfully logged out.'))
        return redirect('/')


class PasswordView(FormView):
    template_name = 'commerce/accounts/password.html'
    form_class = PasswordForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Change password'),
             'url': reverse('commerce_accounts_password')})
        return super(PasswordView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.user.set_password(
            form.cleaned_data.get('new_password', None))
        self.request.user.save()
        messages.success(self.request, _(u'New password successfully saved.'))
        return super(PasswordView, self).form_valid(form)

    def get_success_url(self):
        return reverse('commerce_accounts_password')

    def get_form(self, form_class):
        return form_class(self.request.user, self.request.POST or None)
