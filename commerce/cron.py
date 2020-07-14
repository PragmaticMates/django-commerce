def send_order_reminders():
    from commerce import jobs

    jobs.send_order_reminders.delay()
