from starlette.middleware.cors import CORSMiddleware

from odoo import fields, models
from .routers.payment_redirect import pay


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("app_payment", "HIS Payment API")],
        ondelete={"app_payment": "cascade"},
    )

    def _get_fastapi_routers(self):
        if self.app == "app_payment":
            return [pay]
        return super()._get_fastapi_routers()

    # def _get_app(self):
    #     app = super()._get_app()
    #     app.add_middleware(
    #         CORSMiddleware,
    #         allow_origins=["*"],
    #         allow_credentials=True,
    #         allow_methods=["*"],
    #         allow_headers=["*"],
    #     )
    #     return app
