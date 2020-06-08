CART_IDENTIFIER = 'cart'


def get_cart(request):
    if CART_IDENTIFIER in request.session:
        return request.session[CART_IDENTIFIER]

    request.session[CART_IDENTIFIER] = Cart()
    return request.session[CART_IDENTIFIER]


class Item(object):
    def __init__(self, unique_id, product, quantity):
        self.unique_id = unique_id
        self.product = product
        self.quantity = quantity

    def price(self):
        return self.product.get_price() * self.quantity


class Cart(object):
    def __init__(self):
        self.items = list()
        self.unique_id = 0

    def __iter__(self):
        return self.forward()

    def is_empty(self):
        if len(self.items) is 0:
            return True
        return False

    def total(self):
        total = 0
        for item in self.items:
            total += item.price()
        return total

    def quantity(self):
        quantity = 0
        for item in self.items:
            quantity += item.quantity
        return quantity

    def get(self, product):
        for item in self.items:
            if item.product == product:
                return item
        return None

    def add(self, product, quantity=1, hard_quantity=False):
        # Check if product exists
        for item in self.items:
            if item.product.pk == product.pk:
                if quantity is 0:
                    del self.items[self.items.index(item)]
                    return item
                if hard_quantity is True:
                    item.quantity = quantity
                else:
                    item.quantity += quantity
                return item

        # Product do not exists
        item = Item(self.next_unique_id, product=product, quantity=quantity)
        self.items.append(item)
        return item

    def remove(self, product):
        for item in self.items:
            if item.product == product:
                del self.items[self.items.index(item)]
                return True
        return False

    def clean(self):
        self.items = list()

    def forward(self):
        current_index = 0

        while current_index < len(self.items):
            item = self.items[current_index]
            current_index += 1
            yield item

    def _get_next_unique_id(self):
        self.unique_id += 1
        return self.unique_id
    next_unique_id = property(_get_next_unique_id)
