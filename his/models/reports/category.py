from odoo import models, fields


class ReportCategory(models.Model):
    _name = "his.report_category"
    _description = "Report Category"

    name = fields.Char(string="Name", required=True, translate=True)
    parent_id = fields.Many2one(
        "his.report_category", string="Parent Category", index=True, ondelete="cascade"
    )
    query = fields.Text(string="Query", translate=True)
    filter_domain = fields.Char(string="Filter Domain")


# class OrderDetailReportTransient(models.Model):
#     _name = "his.order_detail_report"
#     _description = "Order Detail Report"
