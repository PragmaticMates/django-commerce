def send_order_reminders():
    from commerce import jobs
    jobs.send_order_reminders.delay()


def cancel_unpaid_orders():
    from commerce import jobs
    jobs.cancel_unpaid_orders.delay()


# TODO: delete old empty carts
