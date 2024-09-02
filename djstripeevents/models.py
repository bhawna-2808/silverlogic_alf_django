from django.db import models

from model_utils import Choices

EventType = Choices(
    ("account.updated", "account__updated", "account.updated"),
    (
        "account.application.deauthorized",
        "account__application__deauthorized",
        "account.application.deauthorized",
    ),
    (
        "account.external_account.created",
        "account__external_account__created",
        "account.external_account.created",
    ),
    (
        "account.external_account.deleted",
        "account__external_account__deleted",
        "account.external_account.deleted",
    ),
    (
        "account.external_account.updated",
        "account__external_account__updated",
        "account.external_account.updated",
    ),
    ("application_fee.created", "application_fee__created", "application_fee.created"),
    (
        "application_fee.refunded",
        "application_fee__refunded",
        "application_fee.refunded",
    ),
    (
        "application_fee.refund.updated",
        "application_fee__refund__updated",
        "application_fee.refund.updated",
    ),
    ("balance.available", "balance__available", "balance.available"),
    (
        "bitcoin.receiver.created",
        "bitcoin__receiver__created",
        "bitcoin.receiver.created",
    ),
    ("bitcoin.receiver.filled", "bitcoin__receiver__filled", "bitcoin.receiver.filled"),
    (
        "bitcoin.receiver.updated",
        "bitcoin__receiver__updated",
        "bitcoin.receiver.updated",
    ),
    (
        "bitcoin.receiver.transaction.created",
        "bitcoin__receiver__transaction__created",
        "bitcoin.receiver.transaction.created",
    ),
    ("charge.captured", "charge__captured", "charge.captured"),
    ("charge.failed", "charge__failed", "charge.failed"),
    ("charge.refunded", "charge__refunded", "charge.refunded"),
    ("charge.succeeded", "charge__succeeded", "charge.succeeded"),
    ("charge.updated", "charge__updated", "charge.updated"),
    ("charge.dispute.closed", "charge__dispute__closed", "charge.dispute.closed"),
    ("charge.dispute.created", "charge__dispute__created", "charge.dispute.created"),
    (
        "charge.dispute.funds_reinstated",
        "charge__dispute__funds_reinstated",
        "charge.dispute.funds_reinstated",
    ),
    (
        "charge.dispute.funds_withdrawn",
        "charge__dispute__funds_withdrawn",
        "charge.dispute.funds_withdrawn",
    ),
    ("charge.dispute.updated", "charge__dispute__updated", "charge.dispute.updated"),
    ("coupon.created", "coupon__created", "coupon.created"),
    ("coupon.deleted", "coupon__deleted", "coupon.deleted"),
    ("coupon.updated", "coupon__updated", "coupon.updated"),
    ("customer.created", "customer__created", "customer.created"),
    ("customer.deleted", "customer__deleted", "customer.deleted"),
    ("customer.updated", "customer__updated", "customer.updated"),
    (
        "customer.discount.created",
        "customer__discount__created",
        "customer.discount.created",
    ),
    (
        "customer.discount.deleted",
        "customer__discount__deleted",
        "customer.discount.deleted",
    ),
    (
        "customer.discount.updated",
        "customer__discount__updated",
        "customer.discount.updated",
    ),
    ("customer.source.created", "customer__source__created", "customer.source.created"),
    ("customer.source.deleted", "customer__source__deleted", "customer.source.deleted"),
    ("customer.source.updated", "customer__source__updated", "customer.source.updated"),
    (
        "customer.subscription.created",
        "customer__subscription__created",
        "customer.subscription.created",
    ),
    (
        "customer.subscription.deleted",
        "customer__subscription__deleted",
        "customer.subscription.deleted",
    ),
    (
        "customer.subscription.trial_will_end",
        "customer__subscription__trial_will_end",
        "customer.subscription.trial_will_end",
    ),
    (
        "customer.subscription.updated",
        "customer__subscription__updated",
        "customer.subscription.updated",
    ),
    ("invoice.created", "invoice__created", "invoice.created"),
    ("invoice.payment_failed", "invoice__payment_failed", "invoice.payment_failed"),
    (
        "invoice.payment_succeeded",
        "invoice__payment_succeeded",
        "invoice.payment_succeeded",
    ),
    ("invoice.updated", "invoice__updated", "invoice.updated"),
    ("invoiceitem.created", "invoiceitem__created", "invoiceitem.created"),
    ("invoiceitem.deleted", "invoiceitem__deleted", "invoiceitem.deleted"),
    ("invoiceitem.updated", "invoiceitem__updated", "invoiceitem.updated"),
    ("order.created", "order__created", "order.created"),
    ("order.payment_failed", "order__payment_failed", "order.payment_failed"),
    ("order.payment_succeeded", "order__payment_succeeded", "order.payment_succeeded"),
    ("order.updated", "order__updated", "order.updated"),
    ("plan.created", "plan__created", "plan.created"),
    ("plan.deleted", "plan__deleted", "plan.deleted"),
    ("plan.updated", "plan__updated", "plan.updated"),
    ("product.created", "product__created", "product.created"),
    ("product.deleted", "product__deleted", "product.deleted"),
    ("product.updated", "product__updated", "product.updated"),
    ("recipient.created", "recipient__created", "recipient.created"),
    ("recipient.deleted", "recipient__deleted", "recipient.deleted"),
    ("recipient.updated", "recipient__updated", "recipient.updated"),
    ("sku.created", "sku__created", "sku.created"),
    ("sku.deleted", "sku__deleted", "sku.deleted"),
    ("sku.updated", "sku__updated", "sku.updated"),
    ("transfer.created", "transfer__created", "transfer.created"),
    ("transfer.failed", "transfer__failed", "transfer.failed"),
    ("transfer.paid", "transfer__paid", "transfer.paid"),
    ("transfer.reversed", "transfer__reversed", "transfer.reversed"),
    ("transfer.updated", "transfer__updated", "transfer.updated"),
    ("ping", "ping", "ping"),
)


class Event(models.Model):
    Type = EventType

    stripe_id = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=255, choices=EventType)
    created = models.DateTimeField()
    data = models.JSONField()
    pending_webhooks = models.PositiveIntegerField()
    request = models.CharField(max_length=255, blank=True)
