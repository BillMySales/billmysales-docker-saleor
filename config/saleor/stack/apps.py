import os
import re
from decimal import Decimal, InvalidOperation

from django.apps import AppConfig


class StackConfig(AppConfig):
    name = "stack"

    def ready(self):
        # Saleor's email templates format amounts with the `price` helper in
        # settings.LANGUAGE_CODE ("en": "CLP19,980"). Use SALEOR_EMAIL_LOCALE
        # (e.g. es_CL: "$19.980") instead. The helper is looked up in the
        # module on every email, so replacing it is enough.
        from babel.core import Locale
        from babel.numbers import format_currency
        import pybars

        from saleor.plugins import email_common

        locale_code = os.environ.get("SALEOR_EMAIL_LOCALE") or "en"
        locale = Locale.parse(locale_code)
        pattern = re.sub(
            "(\xa4+)",
            '<span class="currency">\\1</span>',
            locale.currency_formats["standard"].pattern,
        )

        def price(this, net_amount, gross_amount, currency, display_gross=False):
            try:
                value = Decimal(gross_amount if display_gross else net_amount)
            except (TypeError, InvalidOperation):
                return ""
            return pybars.strlist(
                [format_currency(value, currency, format=pattern, locale=locale)]
            )

        email_common.price = price
