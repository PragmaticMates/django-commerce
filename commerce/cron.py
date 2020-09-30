def send_order_reminders():
    from commerce import jobs
    jobs.send_order_reminders.delay()


def cancel_unpaid_orders():
    from commerce import jobs
    jobs.cancel_unpaid_orders.delay()


def delete_old_empty_carts():
    from commerce import jobs
    jobs.delete_old_empty_carts.delay()


def send_loyalty_reminders():
    from commerce import jobs
    jobs.send_loyalty_reminders.delay()
