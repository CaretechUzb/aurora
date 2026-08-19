from odoo import models, fields, tools, _


class DepartmentPerformance(models.Model):
    _name = "his.performance_stat_by_department_report"
    _description = "Performance statistics by department"
    _auto = False
    _log_access = True

    prescription_date = fields.Date(string="Prescription Date")
    medical_department = fields.Char(string="Medical Department")
    medical_amount = fields.Float(string="Medical Amount")
    discount = fields.Float(string="Discount")
    prescription_name = fields.Many2one("product.template", string="Prescription Name")
    calculated_amount = fields.Float(string="Calculated Amount")
    prescription_discount = fields.Float(string="Prescription Discount")
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
        #     ROW_NUMBER() OVER () as id,
        #     DATE(pv.date) as prescription_date,
        #     hd.name as medical_department,
        #     SUM(CASE WHEN DATE(hod.create_date) = DATE(pv.scheduled_time) AND hd.id = pv.department_id THEN hod.total ELSE 0 END) as medical_amount,
        #     SUM(hod.discount) as discount,
        #     pt.id as prescription_name,
        #     SUM(hod.total) as calculated_amount,
        #     SUM(hod.discount) as prescription_discount,
        #     hd.company_id as company_id,
        #     hd.create_uid as create_uid,
        #     hd.write_uid as write_uid,
        #     hd.create_date as create_date,
        #     hd.create_date as write_date
        # FROM
        #     his_patient_visit pv
        #     LEFT JOIN hr_employee he ON pv.doctor_id = he.id
        #     LEFT JOIN hr_department hd ON he.department_id = hd.id
        #     LEFT JOIN his_patient hp ON hp.id = pv.patient_id
        #     LEFT JOIN res_partner rp ON rp.id = hp.partner_id
        #     LEFT JOIN his_order_detail hod ON hod.patient_visit_id = pv.id
        #     LEFT JOIN product_product pp ON hod.service_id = pp.id
        #     LEFT JOIN product_category pc ON pc.id = pp.categ_id
        #     LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
        # GROUP BY
        #     hd.id, prescription_date, pt.id
        # ORDER BY
        #     hd.name, prescription_date;
        # """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""CREATE view %s as %s """ % (self._table, self._query()))

    def custom_search_filter(self, context=None):
        return {
            "type": "ir.actions.act_window",
            "name": _("Performance statistics by department Search"),
            "res_model": "his.performance_stat_by_department_report_search",
            "context": context,
            "views": [
                [
                    self.env.ref(
                        "his.performance_stat_by_department_report_search_view"
                    ).id,
                    "form",
                ]
            ],
            "target": "new",
        }

    def custom_search_reset(self, context=None):
        action_id = "his.action_performance_stat_by_department_report"
        action = self.env["ir.actions.act_window"]._for_xml_id(action_id)
        action["context"] = {
            "open_filters_callback": "custom_search_filter",
            "reset_filters_callback": "custom_search_reset",
            "use_custom_search": "1",
            "filter_is_active": False,
        }
        action["target"] = "main"
        return action
