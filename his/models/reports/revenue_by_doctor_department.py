from odoo import models, fields, tools, _


class DepartmentDoctorRevenue(models.Model):
    _name = "his.revenue_by_doctor_department_report"
    _description = "Revenue by Department and Doctor"
    _auto = False
    _log_access = True

    doctor = fields.Char(string="Doctor")
    department = fields.Char(string="Department")
    date = fields.Date(string="Date")
    patient = fields.Char(string="Patient")
    discount_total = fields.Float(string="Discount Total")
    amount_total = fields.Float(string="Amount Total")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    create_uid = fields.Many2one("res.users", string="Created by")
    write_uid = fields.Many2one("res.users", string="Last Updated by")
    create_date = fields.Datetime(string="Created on")
    write_date = fields.Datetime(string="Last Updated on")

    def _query(self):
        return """ SELECT * FROM hr_department"""
        # SELECT
        # ROW_NUMBER() OVER () as id,
        # he.name as doctor,
        # hd.name as department,
        # pv.date as date,
        # rp.name as patient,
        # SUM(hod.discount) as discount_total,
        # 0 as amount_total,
        # he.company_id as company_id,
        # he.create_uid as create_uid,
        # he.write_uid as write_uid,
        # he.create_date as create_date,
        # he.create_date as write_date
        # FROM
        # his_patient_visit pv
        # LEFT JOIN hr_employee he ON pv.doctor_id = he.id
        # LEFT JOIN hr_department hd ON he.department_id = hd.id
        # LEFT JOIN his_patient hp ON hp.id = pv.patient_id
        # LEFT JOIN res_partner rp ON rp.id = hp.partner_id
        # LEFT JOIN his_order_detail hod ON hod.patient_visit_id = pv.id
        # GROUP BY
        # he.id, hd.id, pv.date, rp.id
        # ORDER BY
        # he.name, hd.name;"""

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""CREATE view %s as %s """ % (self._table, self._query()))

    def custom_search_filter(self, context=None):
        return {
            "type": "ir.actions.act_window",
            "name": _("Revenue by Department and Doctor Search"),
            "res_model": "his.revenue_by_doctor_department_report_search",
            "context": context,
            "views": [
                [
                    self.env.ref(
                        "his.revenue_by_doctor_department_report_search_view"
                    ).id,
                    "form",
                ]
            ],
            "target": "new",
        }

    def custom_search_reset(self, context=None):
        action_id = "his.action_revenue_by_doctor_department_report"
        action = self.env["ir.actions.act_window"]._for_xml_id(action_id)
        action["context"] = {
            "open_filters_callback": "custom_search_filter",
            "reset_filters_callback": "custom_search_reset",
            "use_custom_search": "1",
            "filter_is_active": False,
        }
        action["target"] = "main"
        return action
