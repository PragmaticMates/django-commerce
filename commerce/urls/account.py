from django.conf.urls import patterns, url

from commerce.views.account import LoginView, LogoutView, \
    RegistrationView, RecoverView, ProfileView, PasswordView


urlpatterns = patterns(
    '',
    url(r'login/$', LoginView.as_view(), name='commerce_accounts_login'),
    url(r'logout/$', LogoutView.as_view(), name='commerce_accounts_logout'),
    url(r'registration/$',
        RegistrationView.as_view(), name='commerce_accounts_registration'),
    url(r'recover/$', RecoverView.as_view(), name='commerce_accounts_recover'),
    url(r'profile/$',
        ProfileView.as_view(), name='commerce_accounts_profile'),
    url(r'password/$',
        PasswordView.as_view(), name='commerce_accounts_password'),
)
