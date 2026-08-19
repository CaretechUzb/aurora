from odoo import _, models, fields, api
from collections import OrderedDict
import io


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    use_emr = fields.Boolean(string="Use EMR")

    def write(self, vals):
        if vals.get("use_emr"):
            if not self.env["ir.config_parameter"].sudo().get_param(self.report_name):
                raise ValueError(
                    _("%s is not found in system parameters"),
                    self.report_name,
                )
        return super(IrActionsReport, self).write(vals)

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report_sudo = self._get_report(report_ref)
        if not report_sudo.use_emr:
            return super(IrActionsReport, self)._render_qweb_pdf(
                report_ref, res_ids, data
            )
        if (
            emr_param := self.env["ir.config_parameter"]
            .sudo()
            .get_param(report_sudo.report_name)
        ):
            emr_report = self.env["report.report"].browse(int(emr_param))
            pdf_content = emr_report.generate_reportbro_pdf(report_sudo.model, res_ids)
            return pdf_content, "pdf"
        else:
            raise ValueError(
                _("%s is not found in system parameters"), report_sudo.report_name
            )
