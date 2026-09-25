"""Admin user and store settings of the Docker stack.

Run by the setup service after the migrations, on every `docker compose up`;
safe to repeat:

- The admin user (SALEOR_ADMIN_EMAIL / SALEOR_ADMIN_PASSWORD), a superuser,
  if missing (its password is only set when it's created).
- Once (marker: site settings private metadata `docker_stack_initialized`),
  adapting the defaults Saleor creates in its migrations: the channel's name,
  currency and country (only while it has no orders or listings), allowing
  unpaid orders (no payment app needed, like a bank transfer: staff marks
  orders as paid), the warehouse's address, the shipping zone and its free
  "Despacho" method, flat tax rate (IVA 19%) with prices including tax,
  Spanish names for the default product type and category, the admin as
  recipient of new order emails, and Spanish email templates and subjects.
  Later changes in the dashboard are kept.
- Every run: the site's domain from SALEOR_URL, the email plugins active when
  SMTP_HOST is set, and their sender from SMTP_FROM / SMTP_FROM_NAME (the SMTP
  server itself comes from USER_EMAIL_URL / EMAIL_URL, see entrypoint.sh).
"""

import os
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from saleor.account.models import Address, StaffNotificationRecipient, User
from saleor.channel.models import Channel
from saleor.checkout.models import Checkout
from saleor.order.models import Order
from saleor.plugins import admin_email, user_email
from saleor.plugins.email_common import DEFAULT_EMAIL_VALUE
from saleor.plugins.models import EmailTemplate, PluginConfiguration
from saleor.product.models import Category, ProductChannelListing, ProductType
from saleor.shipping.models import ShippingMethod, ShippingMethodChannelListing, ShippingZone
from saleor.tax import TaxCalculationStrategy
from saleor.tax.models import TaxClassCountryRate, TaxConfiguration
from saleor.warehouse.models import Warehouse

from ...emails_es import SUBJECTS, translate

MARKER = "docker_stack_initialized"

USER_EMAIL = "mirumee.notifications.user_email"
ADMIN_EMAIL = "mirumee.notifications.admin_email"

# Template field -> default template file of the plugin.
USER_TEMPLATES = {
    "account_confirmation": "confirm.html",
    "account_set_customer_password": "set_customer_password.html",
    "account_delete": "account_delete.html",
    "account_change_email_confirm": "email_changed_notification.html",
    "account_change_email_request": "request_email_change.html",
    "account_password_reset": "password_reset.html",
    "invoice_ready": "send_invoice.html",
    "order_confirmation": "confirm_order.html",
    "order_confirmed": "confirmed_order.html",
    "order_fulfillment_confirmation": "confirm_fulfillment.html",
    "order_fulfillment_update": "update_fulfillment.html",
    "order_payment_confirmation": "confirm_payment.html",
    "order_canceled": "order_cancel.html",
    "order_refund_confirmation": "order_refund.html",
    "send_gift_card": "gift_card.html",
}
ADMIN_TEMPLATES = {
    "staff_order_confirmation_template": "staff_confirm_order.html",
    "set_staff_password_template": "set_password.html",
    "csv_export_success_template": "export_success.html",
    "csv_export_failed_template": "export_failed.html",
    "staff_password_reset_template": "password_reset.html",
}


def env(name: str, default: str = "") -> str:
    return os.environ.get(name) or default


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if not value:
        return default
    return value.lower() in ("1", "true", "yes", "on")


class Command(BaseCommand):
    help = "Admin user and store settings of the Docker stack."

    def handle(self, *args, **options):
        self.admin_user()
        site = Site.objects.get_current()
        settings = site.settings
        if not settings.get_value_from_private_metadata(MARKER):
            with transaction.atomic():
                self.initial_settings(site)
                # Marker last: a failed run is repeated.
                settings.store_value_in_private_metadata({MARKER: "1"})
                settings.save(update_fields=["private_metadata"])
        self.environment(site)
        self.stdout.write("Store settings OK")

    def admin_user(self):
        email = env("SALEOR_ADMIN_EMAIL")
        if User.objects.filter(email=email).exists():
            return
        os.environ["DJANGO_SUPERUSER_PASSWORD"] = env("SALEOR_ADMIN_PASSWORD")
        call_command("createsuperuser", interactive=False, email=email, verbosity=0)
        self.stdout.write(f"Admin user {email} created")

    def initial_settings(self, site):
        currency = env("SALEOR_CURRENCY", "CLP").upper()
        country = env("DEFAULT_COUNTRY", "CL").upper()
        slug = env("DEFAULT_CHANNEL_SLUG", "default-channel")
        self.stdout.write(f"Initial store settings ({country}, {currency})")

        site.name = env("SALEOR_STORE_NAME", "Saleor")
        site.save(update_fields=["name"])

        channel = Channel.objects.filter(slug=slug).first()
        if channel is None:
            channel = Channel.objects.create(
                name=env("SALEOR_CHANNEL_NAME", "Tienda"),
                slug=slug,
                currency_code=currency,
                default_country=country,
                is_active=True,
            )
        in_use = (
            Order.objects.filter(channel=channel).exists()
            or Checkout.objects.filter(channel=channel).exists()
            or ProductChannelListing.objects.filter(channel=channel).exists()
        )
        if channel.currency_code != currency and in_use:
            self.stderr.write(
                f"Channel {slug} already has orders or products in "
                f"{channel.currency_code}: currency not changed"
            )
        else:
            channel.currency_code = currency
        channel.name = env("SALEOR_CHANNEL_NAME", "Tienda")
        channel.default_country = country
        channel.is_active = True
        channel.allow_unpaid_orders = env_bool("SALEOR_ALLOW_UNPAID_ORDERS", True)
        channel.save()

        # Warehouse (Saleor's default one, or a new one).
        warehouse = Warehouse.objects.filter(slug="default-warehouse").first()
        if warehouse is None:
            warehouse = Warehouse.objects.create(
                name="Bodega",
                slug="default-warehouse",
                address=Address.objects.create(country=country),
            )
        warehouse.name = "Bodega"
        warehouse.email = env("SMTP_FROM", "")
        warehouse.save()
        address = warehouse.address
        address.company_name = site.name
        address.city = env("SALEOR_CITY", "Santiago")
        address.country = country
        address.save()
        warehouse.channels.add(channel)

        # Shipping zone for the country with one free method.
        zone = ShippingZone.objects.filter(name__in=["Default", "Chile"]).first()
        if zone is None:
            zone = ShippingZone.objects.create(name="Chile", countries=[country])
        zone.name = env("SALEOR_ZONE_NAME", "Chile")
        zone.countries = [country]
        zone.default = False
        zone.save()
        zone.channels.add(channel)
        zone.warehouses.add(warehouse)
        method = ShippingMethod.objects.filter(shipping_zone=zone).first()
        if method is None:
            method = ShippingMethod.objects.create(
                name="Despacho", type="price", shipping_zone=zone
            )
        method.name = "Despacho"
        method.save(update_fields=["name"])
        ShippingMethodChannelListing.objects.update_or_create(
            shipping_method=method,
            channel=channel,
            defaults={"currency": channel.currency_code, "price_amount": Decimal(0)},
        )
        ShippingMethodChannelListing.objects.filter(channel=channel).update(
            currency=channel.currency_code
        )

        # Taxes: flat rate for the country, prices entered including tax.
        tax_config, _ = TaxConfiguration.objects.get_or_create(channel=channel)
        tax_config.charge_taxes = True
        tax_config.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
        tax_config.prices_entered_with_tax = env_bool("SALEOR_PRICES_INCLUDE_TAX", True)
        tax_config.display_gross_prices = True
        tax_config.save()
        rate = env("SALEOR_TAX_RATE", "")
        if rate:
            TaxClassCountryRate.objects.update_or_create(
                country=country, tax_class=None, defaults={"rate": Decimal(rate)}
            )

        ProductType.objects.filter(slug="default-type").update(name="Producto")
        Category.objects.filter(slug="default-category").update(name="General")

        admin = User.objects.filter(email=env("SALEOR_ADMIN_EMAIL")).first()
        if admin and not StaffNotificationRecipient.objects.exists():
            StaffNotificationRecipient.objects.create(user=admin)

        if env_bool("SALEOR_EMAILS_SPANISH", True):
            self.spanish_emails(channel)

    def plugin_config(self, identifier, name, channel):
        config, _ = PluginConfiguration.objects.get_or_create(
            identifier=identifier, channel=channel, defaults={"name": name}
        )
        return config

    def spanish_emails(self, channel):
        for identifier, name, module, templates, config_channel in (
            (USER_EMAIL, "User emails", user_email, USER_TEMPLATES, channel),
            (ADMIN_EMAIL, "Admin emails", admin_email, ADMIN_TEMPLATES, None),
        ):
            config = self.plugin_config(identifier, name, config_channel)
            directory = Path(module.__file__).parent / "default_email_templates"
            for field, file_name in templates.items():
                # Saleor's migrations store "DEFAULT" (use the file) for the
                # default channel: replace only those, never an edited one.
                current = config.email_templates.filter(name=field).first()
                if current and current.value != DEFAULT_EMAIL_VALUE:
                    continue
                html = translate((directory / file_name).read_text())
                EmailTemplate.objects.update_or_create(
                    plugin_configuration=config, name=field, defaults={"value": html}
                )
            subjects = {
                key: value
                for key, value in SUBJECTS.items()
                if key.replace("_subject", "") in templates
                or key.replace("_subject", "_template") in templates
            }
            self.set_config_items(config, subjects)
            config.save()
        self.stdout.write("Spanish email templates stored")

    @staticmethod
    def set_config_items(config, values: dict) -> bool:
        """Set configuration items (list of name/value); True if changed."""
        items = list(config.configuration or [])
        by_name = {item["name"]: item for item in items}
        changed = False
        for key, value in values.items():
            item = by_name.get(key)
            if item is None:
                items.append({"name": key, "value": value})
                changed = True
            elif item.get("value") != value:
                item["value"] = value
                changed = True
        config.configuration = items
        return changed

    def environment(self, site):
        url = urlsplit(env("SALEOR_URL"))
        if site.domain != url.netloc:
            site.domain = url.netloc
            site.save(update_fields=["domain"])

        settings = site.settings
        sender = env("SMTP_FROM", "noreply@example.com")
        sender_name = env("SMTP_FROM_NAME", site.name)
        if (
            settings.default_mail_sender_address != sender
            or settings.default_mail_sender_name != sender_name
        ):
            settings.default_mail_sender_address = sender
            settings.default_mail_sender_name = sender_name
            settings.save(
                update_fields=["default_mail_sender_address", "default_mail_sender_name"]
            )

        active = bool(env("SMTP_HOST"))
        slug = env("DEFAULT_CHANNEL_SLUG", "default-channel")
        channels = list(Channel.objects.all())
        targets = [(USER_EMAIL, "User emails", channel) for channel in channels]
        targets.append((ADMIN_EMAIL, "Admin emails", None))
        for identifier, name, channel in targets:
            # Only the stack's channel is set up; other channels keep their
            # own plugin configuration (created in the dashboard).
            if channel is not None and channel.slug != slug:
                continue
            config = self.plugin_config(identifier, name, channel)
            changed = self.set_config_items(
                config, {"sender_name": sender_name, "sender_address": sender}
            )
            if config.active != active:
                config.active = active
                changed = True
            if changed:
                config.save()
                state = "active" if active else "inactive (no SMTP_HOST)"
                self.stdout.write(f"{name}: {state}, sender {sender}")
