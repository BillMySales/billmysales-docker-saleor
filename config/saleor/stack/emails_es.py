"""Spanish texts for Saleor's built-in email plugins.

Saleor's default email templates (saleor/plugins/*/default_email_templates)
are compiled MJML with English texts. `translate()` replaces the texts
between HTML tags, keeping the markup and the Handlebars expressions, so the
result follows the image's own templates. The setup command stores the
result as the plugins' templates once; they can be edited in the dashboard
afterwards (Configuration > Plugins).
"""

import re

SUBJECTS = {
    # UserEmailPlugin (customers).
    "account_confirmation_subject": "Confirma tu cuenta en {{ site_name }}",
    "account_set_customer_password_subject": "Crea tu contraseña en {{ site_name }}",
    "account_delete_subject": "Eliminar tu cuenta",
    "account_change_email_confirm_subject": "Tu correo fue cambiado",
    "account_change_email_request_subject": "Confirma el cambio de correo",
    "account_password_reset_subject": "Restablece tu contraseña",
    "invoice_ready_subject": "Tu factura",
    "order_confirmation_subject": "Detalle del pedido N° {{ order.number }}",
    "order_confirmed_subject": "Pedido N° {{ order.number }} confirmado",
    "order_fulfillment_confirmation_subject": "Tu pedido N° {{ order.number }} fue despachado",
    "order_fulfillment_update_subject": "Actualización del despacho del pedido N° {{ order.number }}",
    "order_payment_confirmation_subject": "Pago del pedido N° {{ order.number }}",
    "order_canceled_subject": "Pedido N° {{ order.number }} cancelado",
    "order_refund_confirmation_subject": "Reembolso del pedido N° {{ order.number }}",
    "send_gift_card_subject": "Tarjeta de regalo de {{ site_name }}",
    # AdminEmailPlugin (staff).
    "staff_order_confirmation_subject": "Nuevo pedido N° {{ order.number }}",
    "set_staff_password_subject": "Invitación al panel de administración",
    "csv_export_success_subject": "Tu exportación de {{ data_type }} está lista",
    "csv_export_failed_subject": "Falló la exportación de {{ data_type }}",
    "staff_password_reset_subject": "Restablece tu contraseña del panel",
}

# Whole texts between two tags (whitespace-normalized).
TEXTS = {
    "Billing address": "Dirección de facturación",
    "Discount": "Descuento",
    "Download data": "Descargar datos",
    "Hello there!": "¡Hola!",
    "Hello,": "Hola:",
    "Hi!": "¡Hola!",
    "Item": "Producto",
    "Per unit": "Por unidad",
    "Qty": "Cant.",
    "Quantity": "Cantidad",
    "Reset my password": "Restablecer mi contraseña",
    "See order": "Ver pedido",
    "Set my password": "Crear mi contraseña",
    "Shipping": "Despacho",
    "Shipping address": "Dirección de despacho",
    "Thank you!": "¡Gracias!",
    "Have a great day!": "¡Que tengas un buen día!",
    "Have a great day and thank you!": "¡Que tengas un buen día, y gracias!",
    "The details of the order": "Detalle del pedido",
}

# Phrases replaced inside texts (longest first, so shorter phrases don't
# break longer ones).
PHRASES = [
    ("A payment of {{amount}} {{currency}} has been refunded for your order.",
     "Se reembolsó un pago de {{amount}} {{currency}} de tu pedido."),
    ("Certain messages, like this one, are essential to service operations.",
     "Algunos mensajes, como este, son necesarios para el funcionamiento del servicio."),
    ("Click the link below to delete your account. Please note that this action is permanent and cannot be reversed.",
     "Haz clic en el enlace de abajo para eliminar tu cuenta. Esta acción es permanente y no se puede deshacer."),
    ("Click the link below to set up your password.",
     "Haz clic en el enlace de abajo para crear tu contraseña."),
    ("Didn&apos;t request a reset? Ignore this message (or reply to let us know).",
     "¿No lo solicitaste? Ignora este mensaje."),
    ("Enter the gift card code at checkout to redeem your gift card.",
     "Ingresa el código de la tarjeta de regalo al pagar para usarla."),
    ("Gift card code:", "Código de la tarjeta de regalo:"),
    ("If you didn't request this change, please contact the administrator.",
     "Si no solicitaste este cambio, contacta al administrador."),
    ("In order to download invoice {{number}}, click the link below.",
     "Para descargar la factura {{number}}, haz clic en el enlace de abajo."),
    ("In order to log into {{ site_name }}, you have to confirm your email address first. Please click the link below to do so and log into your account.",
     "Para iniciar sesión en {{ site_name }}, primero debes confirmar tu correo. Haz clic en el enlace de abajo para confirmarlo e ingresar a tu cuenta."),
    ("It can be safely ignored if you did not request a password reset. Click the link below to reset your password.",
     "Si no solicitaste restablecer tu contraseña, puedes ignorar este mensaje. Haz clic en el enlace de abajo para restablecerla."),
    ("It can be safely ignored if you did not request an email change. Click the link below to confirm new email address.",
     "Si no solicitaste cambiar tu correo, puedes ignorar este mensaje. Haz clic en el enlace de abajo para confirmar la nueva dirección."),
    ("New order just came in!", "¡Llegó un pedido nuevo!"),
    ("Our appolgies and thank you.", "Te pedimos disculpas, y gracias."),
    ("Sincerely,", "Saludos,"),
    ("Someone just added you to a Saleor project. That means you’ve got things to build, break, or ship (preferably in that order).",
     "Te agregaron como usuario del panel de administración de la tienda."),
    ("Someone placed a new order in your store.", "Alguien hizo un pedido nuevo en tu tienda."),
    ("Sorry, we couldn't finish exporting {{data_type}} due to unexpected errors. Please try again.",
     "No se pudo terminar la exportación de {{data_type}} por un error inesperado. Inténtalo de nuevo."),
    ("Thank you for your payment. Your payment was successfully processed.",
     "Gracias por tu pago. Tu pago fue procesado con éxito."),
    ("This is an automatically generated e-mail, please do not reply.",
     "Este correo fue generado automáticamente, por favor no respondas."),
    ("This link expires in 24 hours. If you miss the window, please reset your password again.",
     "Este enlace vence en 24 horas. Si vence, solicita restablecer tu contraseña de nuevo."),
    ("To download your {{data_type}} data, simply click the button below.",
     "Para descargar los datos de {{data_type}}, haz clic en el botón de abajo."),
    ("To get in, you’ll need to set a password. Just click the button below.",
     "Para ingresar, debes crear una contraseña. Haz clic en el botón de abajo."),
    ("To reset your password, simply click the “Reset my password” button below.",
     "Para restablecer tu contraseña, haz clic en el botón “Restablecer mi contraseña” de abajo."),
    ('To see order details please click the button "See order" below.',
     "Para ver el detalle del pedido, haz clic en el botón “Ver pedido” de abajo."),
    ("To see order details please click the button &quot;See order&quot; below.",
     "Para ver el detalle del pedido, haz clic en el botón “Ver pedido” de abajo."),
    ("Use this card as payment for anything you like in {{ site_name }}.",
     "Usa esta tarjeta para pagar lo que quieras en {{ site_name }}."),
    ("We received your dashboard password reset request.",
     "Recibimos tu solicitud para restablecer la contraseña del panel."),
    ("We're happy to let you know that your file with {{data_type}} data is ready to download.",
     "Tu archivo con los datos de {{data_type}} está listo para descargar."),
    ("You're receiving this e-mail because you have to set password for your customer account at {{site_name}}.",
     "Recibes este correo porque debes crear la contraseña de tu cuenta de cliente en {{site_name}}."),
    ("You're receiving this e-mail because you or someone else has changed email for your user account at {{ site_name }}.",
     "Recibes este correo porque tú u otra persona cambió el correo de tu cuenta en {{ site_name }}."),
    ("You're receiving this e-mail because you or someone else has requested a deletion of your user account at {{ site_name }}.",
     "Recibes este correo porque tú u otra persona solicitó eliminar tu cuenta en {{ site_name }}."),
    ("You're receiving this e-mail because you or someone else has requested a password for your user account at {{site_name}}.",
     "Recibes este correo porque tú u otra persona solicitó una contraseña para tu cuenta en {{site_name}}."),
    ("You're receiving this e-mail because you or someone else has requested an email change for your user account at {{site_name}}.",
     "Recibes este correo porque tú u otra persona solicitó cambiar el correo de tu cuenta en {{site_name}}."),
    ("Your order #{{order.number}} has been canceled.", "Tu pedido N° {{order.number}} fue cancelado."),
    ("Your shipping status has been updated. Below is the list of ordered products that have been updated with new tracking number.",
     "El estado de tu despacho fue actualizado. Abajo están los productos del pedido con el nuevo número de seguimiento."),
    ("You can track your shipment with {{ fulfillment.tracking_number }} code.",
     "Puedes seguir tu despacho con el código {{ fulfillment.tracking_number }}."),
    ("You can track your shipment with {{fulfillment.tracking_number}} code.",
     "Puedes seguir tu despacho con el código {{fulfillment.tracking_number}}."),
    # Followed by a link with the tracking number, then "link.".
    ("You can track your shipment with", "Puedes seguir tu despacho en"),
    ("link. {{else}}", ". {{else}}"),
    ("You’re in—welcome to Saleor Commerce!", "¡Bienvenido al panel de administración!"),
    ("No billing address", "Sin dirección de facturación"),
    ("No shipping required", "No requiere despacho"),
    ("Taxes (included)", "Impuestos (incluidos)"),
    ("{{else}} Taxes {{/if}}", "{{else}} Impuestos {{/if}}"),
    ("Thank you for your order. Below is the list of fulfilled products. To see your order details please visit:",
     "Gracias por tu pedido. Abajo están los productos despachados. Para ver el detalle de tu pedido, visita:"),
    ("Thank you for your order. Below is the list of ordered products. To see your payment details please visit:",
     "Gracias por tu pedido. Abajo están los productos pedidos. Para ver el detalle de tu pago, visita:"),
    ("Your order has been confirmed by staff. To see your order details please visit:",
     "Tu pedido fue confirmado. Para ver el detalle de tu pedido, visita:"),
    ("Thank you for your order. Below is the list of fulfilled products.",
     "Gracias por tu pedido. Abajo están los productos despachados."),
    ("Thank you for your order. Below is the list of ordered products.",
     "Gracias por tu pedido. Abajo están los productos pedidos."),
    ("Your order has been confirmed by staff. Below is the list of ordered products.",
     "Tu pedido fue confirmado. Abajo están los productos pedidos."),
    ("Hi, {{ user.first_name }}", "Hola, {{ user.first_name }}"),
    ("Hi, {{ recipient_email }}", "Hola, {{ recipient_email }}"),
    ("Here is your gift card!", "¡Aquí está tu tarjeta de regalo!"),
]
PHRASES.sort(key=lambda item: len(item[0]), reverse=True)

_TEXT_RE = re.compile(r">([^<]+)<")


def _translate_text(match: re.Match) -> str:
    raw = match.group(1)
    text = " ".join(raw.split())
    if not text:
        return match.group(0)
    new = TEXTS.get(text)
    if new is None:
        new = text
        for english, spanish in PHRASES:
            new = new.replace(english, spanish)
    if new == text:
        return match.group(0)
    return f">{new}<"


def translate(html: str) -> str:
    """Spanish version of a default template (only the body is changed)."""
    head, sep, body = html.partition("<body")
    if not sep:
        return _TEXT_RE.sub(_translate_text, html)
    return head.replace('lang="en"', 'lang="es"') + sep + _TEXT_RE.sub(
        _translate_text, body
    )


def untranslated(html: str) -> list[str]:
    """Texts that still look English (for the setup's check)."""
    body = html.partition("<body")[2] or html
    words = re.compile(
        r"\b(the|your|you|order|please|click|thank|have|has|been|below|this|with)\b",
        re.IGNORECASE,
    )
    found = []
    for match in _TEXT_RE.finditer(body):
        text = " ".join(match.group(1).split())
        plain = re.sub(r"\{\{[^}]*\}\}", "", text)
        if words.search(plain):
            found.append(text)
    return found
