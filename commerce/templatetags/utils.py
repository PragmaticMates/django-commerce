# -*- coding: utf-8

from django.core.urlresolvers import resolve, Resolver404
from django.template import Library

from commerce.forms.account import LoginForm, RegistrationForm, RecoverForm
from commerce.forms.filter import FilterForm
from commerce.models.catalog import Catalog
from commerce.utils.cart import get_cart
from commerce.app_settings import COMMERCE_CURRENCY

register = Library()
URL_NAME = 'commerce_catalogs_detail'


@register.inclusion_tag('commerce/helpers/pagination.html', takes_context=True)
def paginator(context, objects, page_ident='page', anchor=None, adjacent=2):
    page_range = objects.paginator.page_range
    number = objects.number

    page_numbers = [n for n in range(number - adjacent, number + adjacent + 1)
                    if n > 0 and n <= len(page_range)]

    return {
        'anchor': anchor,
        'request': context.get('request', None),
        'page_ident': page_ident,
        'results_per_page': objects.paginator.per_page,
        'page': objects.number,
        'pages': page_range,
        'count': len(page_range),
        'page_numbers': page_numbers,
        'next': objects.next_page_number,
        'previous': objects.previous_page_number,
        'has_next': objects.has_next,
        'has_previous': objects.has_previous,
        'show_first': 1 not in page_numbers,
        'show_last': False if len(page_range) - number <= adjacent else True
    }


@register.inclusion_tag(
    'commerce/cart/templatetags/block.html', takes_context=True)
def cart_block(context):
    request = context['request']
    return {
        'cart': get_cart(request)
    }


@register.inclusion_tag(
    'commerce/helpers/pages-block.html', takes_context=True)
def pages_block(context):
    request = context['request']
    return {
        'slug': request.path_info,
    }


@register.inclusion_tag(
    'commerce/catalogs/templatetags/block.html', takes_context=True)
def catalogs_block(context):
    catalogs = Catalog.objects.all()
    request = context['request']
    active = None

    try:
        view = resolve(request.path)
        if view.url_name == URL_NAME:
            active = view.kwargs['slug']
    except Resolver404:
        view = ''

    return {
        'object_list': catalogs,
        'active': active
    }


@register.inclusion_tag(
    'commerce/accounts/templatetags/modals.html', takes_context=True)
def modals(context):
    return {
        'login_form': LoginForm(),
        'registration_form': RegistrationForm(),
        'recover_form': RecoverForm(),
    }


@register.inclusion_tag(
    'commerce/products/templatetags/filter.html', takes_context=True)
def filter(context):
    return {
        'form': FilterForm(request=context['request']),
    }

@register.filter(name='format_price')
def format_price(value):
    currency = COMMERCE_CURRENCY

    if value is None:
        return '%.2f %s' % (0, currency)

    if type(value) is str:
        return '%.2f %s' % (0, currency)
    return '%.2f %s' % (value, currency)
