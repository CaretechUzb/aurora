from odoo import models, fields, tools, _


class NumberPatient(models.Model):
    _name = "his.number_of_patients_report"
    _description = "NUMBER OF PATIENTS(Monthly Report)"
    _auto = False
    _log_access = True

    month = fields.Date(string="Date")
    department = fields.Many2one(
        "hr.department", string="Department", check_company=True
    )
    patient_count = fields.Integer(string="Patient Count")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    create_uid = fields.Many2one("res.users", string="Created by")
    write_uid = fields.Many2one("res.users", string="Last Updated by")
    create_date = fields.Datetime(string="Created on")
    write_date = fields.Datetime(string="Last Updated on")

    def _query(self):
        return """ SELECT * FROM hr_department"""
        #         SELECT
        #             ROW_NUMBER() OVER () AS id,
        #             DATE_TRUNC('month', pv.date) AS month,
        #             d.id AS department,
        #             COUNT(DISTINCT pv.patient_id) AS patient_count,
        #             d.company_id as company_id,
        #             d.create_uid as create_uid,
        #             d.write_uid as write_uid,
        #             d.create_date as create_date,
        #             d.create_date as write_date
        #         FROM
        #         hr_department d
        #         LEFT JOIN his_patient_visit pv ON pv.department_id = d.id
        #         GROUP BY
        #             month,
        #             d.id, d.company_id
        #         ORDER BY
        #             month,
        #             d.name;
        # """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""CREATE view %s as %s """ % (self._table, self._query()))

    def custom_search_filter(self, context=None):
        return {
            "type": "ir.actions.act_window",
            "name": _("NUMBER OF PATIENTS(Monthly Report) Search"),
            "res_model": "his.number_of_patients_search",
            "context": context,
            "views": [[self.env.ref("his.number_of_patients_search_view").id, "form"]],
            "target": "new",
        }

    def custom_search_reset(self, context=None):
        action_id = "his.action_number_of_patients_report"
        action = self.env["ir.actions.act_window"]._for_xml_id(action_id)
        action["context"] = {
            "open_filters_callback": "custom_search_filter",
            "reset_filters_callback": "custom_search_reset",
            "use_custom_search": "1",
            "filter_is_active": False,
        }
        action["target"] = "main"
        return action
