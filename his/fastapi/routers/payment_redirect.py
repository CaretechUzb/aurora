from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import RedirectResponse

from odoo.addons.fastapi.dependencies import odoo_env
from odoo.api import Environment

pay = APIRouter()


@pay.get("/payment/status/{invoice_id}")
async def payme_status(
    invoice_id: int,
    env: Environment = Depends(odoo_env),
):
    if not invoice_id:
        return Response(status_code=400, content="Invoice ID is required")

    invoice = env["account.move"].sudo().browse(int(invoice_id))
    if not invoice.exists():
        return Response(status_code=404, content="Invoice not found")

    base_url = env["ir.config_parameter"].sudo().get_param("web.base.url")
    if invoice.payment_state == "paid":
        return RedirectResponse(url=f"{base_url}/myprofile?success")
    else:
        return RedirectResponse(url=f"{base_url}/myprofile?not_paid")


#
# @pay.get("/{provider}/{invoice_id}")
# async def payme_invoice_redirect(
#         provider: str,
#         invoice_id: int,
#         env: Environment = Depends(odoo_env),
#         lang: str = "ru",
#         callback: bool = False
#     ):
#     if provider == 'payme':
#         try:
#             is_ok, response = env['payment.provider'].sudo()._payme_get_api_url_full(invoice_id, callback, lang)
#             if not is_ok:
#                 raise HTTPException(status_code=404, detail=response)
#         except Exception:
#             raise HTTPException(status_code=404, detail={"error": "Provider not found"})
#
#     elif provider == 'click':
#         try:
#             is_ok, response = env['payment.provider'].sudo()._click_get_api_url_full(invoice_id, lang, callback)
#             if not is_ok:
#                 raise HTTPException(status_code=404, detail=response)
#         except Exception:
#             raise HTTPException(status_code=404, detail={"error": "Provider not found"})
#     else:
#         # base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
#         # response = f"{base_url}/{provider}/{invoice_id}"
#         response = ""
#
#     return RedirectResponse(
#         url=response,
#         status_code=303
#     )
