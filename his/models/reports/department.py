from odoo import _, models, fields, tools


class DailyPerformanceTransient(models.Model):
    _name = "his.department_performance"
    _description = "Department Performance Total"
    _auto = False
    _log_access = True

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    order_count = fields.Integer(string="Order Count")
    number_of_patient = fields.Integer(string="Number of Patient")
    total_performance = fields.Float(string="Total Performance")
    discount_amount = fields.Float(string="Discount Amount")
    total_amount = fields.Float(string="Total Amount")
    visit_date = fields.Date(string="Date")
    department_id = fields.Many2one("hr.department", string="Department")
    name = fields.Char(string="Name")
    create_uid = fields.Many2one("res.users", string="Create User")
    create_date = fields.Datetime(string="Create Date")
    write_uid = fields.Many2one("res.users", string="Write User")
    write_date = fields.Datetime(string="Write Date")

    def _query(self):
        return """ SELECT * FROM hr_department"""
        # SELECT
        #     ROW_NUMBER() OVER () as id,
        #     d.id as department_id,
        #     d.name as name,
        #     0 as order_count,
        #     0 as number_of_patient,
        #     0 as total_performance,
        #     0 as total_amount,
        #     0 as discount_amount,
        #     d.create_uid as create_uid,
        #     d.write_uid as write_uid,
        #     date(p.scheduled_time) as visit_date,
        #     d.create_date as create_date,
        #     d.write_date as write_date,
        #     d.company_id as company_id
        # FROM
        #     his_patient_visit p
        #     LEFT JOIN hr_department d ON p.department_id = d.id
        # GROUP BY
        #     d.id, visit_date
        # """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""CREATE view %s as %s """ % (self._table, self._query()))

    def action_show_report(self):
        pass

    #         fields_to_search = {
    #             'department_id': self.department_id.id,
    #             'visit_date': self.visit_date
    #         }

    #         search_domain = [ (field, '=', value)
    #             for field, value in fields_to_search.items() if value]

    #         result = self.env['his.order_detail_report'].search(search_domain)

    #         default_datas = {
    #             'default_department_id': self.department_id.id,
    #             'default_visit_date': self.visit_date,
    #             'default_result_order_detail': [(6, 0, result.ids)],
    #             'default_disable_departments': True,
    #             'default_company_id': self.company_id.id,
    #         }

    #         return {
    #             'name': _('Order Details'),
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'his.daily_performance_wizard',
    #             'view_mode': 'form',
    #             'views': [[False, 'form']],
    #             'context': default_datas,
    #             'target': 'new'
    #         }
