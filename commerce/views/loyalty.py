from django.views.generic import TemplateView


class LoyaltyProgramView(TemplateView):
    template_name = 'commerce/loyalty.html'
