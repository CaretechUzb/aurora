from odoo import fields, models, _, Command, tools, api
import logging

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    @api.model
    def _build_wkhtmltopdf_args(
        self,
        paperformat_id,
        landscape,
        specific_paperformat_args=None,
        set_viewport_size=False,
    ):
        args = super(IrActionsReport, self)._build_wkhtmltopdf_args(
            paperformat_id, landscape, specific_paperformat_args, set_viewport_size
        )
        if paperformat_id:
            if paperformat_id.enable_forms:
                args.extend(["--enable-forms"])
        args.remove("--quiet")
        return args
