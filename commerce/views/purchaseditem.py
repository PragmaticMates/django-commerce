import os

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from filer.models import File, Image
from filer.settings import FILER_IS_PUBLIC_DEFAULT

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
        file_obj = form.cleaned_data['file']
        folder = None  # unsorted

        f = self.import_file(file_obj, folder)

        # f.name = str(file_obj)
        f.description = f'{self.purchased_item.order}: {self.purchased_item}'
        f.owner = self.request.user
        f.save(update_fields=['description', 'owner'])

        # thumbnail_180_options = {
        #     'size': (180, 180),
        #     'crop': True,
        #     'upscale': True,
        # }
        # thumbnail_180 = f.file.get_thumbnail(thumbnail_180_options)

        self.purchased_item.files.add(f)

        return redirect(self.get_back_url())

    def form_invalid(self, form):
        messages.error(self.request, _('Error during upload'))
        return redirect(self.get_back_url())

    def import_file(self, file_obj, folder):
        """
        Create a File or an Image into the given folder
        """
        try:
            iext = os.path.splitext(file_obj.name)[1].lower()
        except:  # noqa
            iext = ''
        if iext in ['.jpg', '.jpeg', '.png', '.gif']:
            obj, created = Image.objects.get_or_create(
                original_filename=file_obj.name,
                file=file_obj,
                folder=folder,
                is_public=FILER_IS_PUBLIC_DEFAULT)
        else:
            obj, created = File.objects.get_or_create(
                original_filename=file_obj.name,
                file=file_obj,
                folder=folder,
                is_public=FILER_IS_PUBLIC_DEFAULT)
        return obj
