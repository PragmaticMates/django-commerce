from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from filer.models import File

from commerce.forms import PurchasedItemFileForm
from commerce.models import PurchasedItem


class UploadFileToPurchasedItem(FormView):
    purchased_item = None
    form_class = PurchasedItemFileForm

    def get_back_url(self):
        return self.request.GET.get('back_url', self.purchased_item.order.get_absolute_url() if self.purchased_item else '/')

    def form_valid(self, form):
        purchased_item_id = form.cleaned_data['purchased_item_id']
        self.purchased_item = PurchasedItem.objects.get(id=purchased_item_id)
        file = form.cleaned_data['file']

        f = File.objects.create(
            file=file,
            name=str(file),
            description=str(self.purchased_item),
            owner=self.request.user,
        )

        self.purchased_item.files.add(f)

        return redirect(self.get_back_url())

    def form_invalid(self, form):
        messages.error(self.request, _('Error during upload'))
        return redirect(self.get_back_url())
