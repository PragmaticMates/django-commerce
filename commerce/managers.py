class PaymentManager(object):
    def __init__(self, order):
        self.order = order

    def get_payment_url(self):
        raise NotImplementedError()

    def render_payment_button(self):
        raise NotImplementedError()

    def render_payment_information(self):
        raise NotImplementedError()

    def handle_payment_result(self, data):
        raise NotImplementedError()
