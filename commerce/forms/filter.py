from django import forms
from django.utils.translation import ugettext_lazy as _


class FilterForm(forms.Form):
    SORT_DATE = 'DATE'
    SORT_PRICE = 'PRICE'
    SORT_TITLE = 'TITLE'
    SORTS = (
        (SORT_DATE, _(u'Creation date')),
        (SORT_PRICE, _(u'Price')),
        (SORT_TITLE, _(u'Title')),
    )
    ASC = 'ASC'
    DESC = 'DESC'
    WAYS = (
        ('ASC', _(u'Ascending')),
        ('DESC', _(u'Descending')),
    )

    PAGINATE_BY = (
        ('10', 10),
        ('20', 20),
        ('30', 30),
        ('50', 40),
    )

    PROPERTY_TOP = 'TOP'
    PROPERTY_DISCOUNT = 'DISCOUNT'
    PROPERTY_NEW = 'NEW'
    PROPERTIES = (
        (PROPERTY_TOP, _(u'Top products')),
        (PROPERTY_DISCOUNT, _(u'Discounted products')),
        (PROPERTY_NEW, _(u'New products')),
    )

    sort = forms.CharField(
        label=_(u'Sort'), widget=forms.Select(choices=SORTS), required=False)
    ordering = forms.CharField(
        label=_(u'Ordering'), widget=forms.RadioSelect(choices=WAYS), required=False, initial=ASC)
    paginate_by = forms.CharField(
        label=_(u'Paginate by'), widget=forms.Select(choices=PAGINATE_BY), required=False, initial='10')
    properties = forms.CharField(
        label=_(u'Properties'), widget=forms.CheckboxSelectMultiple(choices=PROPERTIES), required=False)

    def __init__(self,  request, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        if 'properties' in request.GET:
            self.initial['properties'] = request.GET.getlist('properties')
        if 'sort' in request.GET:
            self.initial['sort'] = request.GET.get('sort')
        if 'ordering' in request.GET:
            self.initial['ordering'] = request.GET.get('ordering', self.ASC)
        if 'paginate_by' in request.GET:
            self.initial['paginate_by'] = int(request.GET['paginate_by'])
