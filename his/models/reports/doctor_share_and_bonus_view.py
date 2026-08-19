from odoo import api, fields, models, tools, _
import base64
import pandas as pd
from io import BytesIO
from odoo.exceptions import UserError


class DoctorShareAndBonusView(models.Model):
    _name = "his.doctor_share_and_bonus_view"
    _description = "Doctor Share And Bonus Report View"
    _auto = False
    _rec_name = "id"
    _order = "id desc"

    id = fields.Integer(string="ID", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)

    visit_patient_type = fields.Selection(
        [("opd", "OPD"), ("er", "ER"), ("ipd", "IPD")],
        string="Visit Patient Type",
        readonly=True,
    )
    patient_id = fields.Many2one(
        "his.patient",
        string="Patient",
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        readonly=True,
    )

    scheduled_date_time = fields.Char(string="Scheduled Date Time", readonly=True)
    price_total = fields.Monetary(string="Price Total", readonly=True)
    price_unit = fields.Monetary(string="Price Unit", readonly=True)
    service_id = fields.Many2one(
        "product.product",
        string="Service",
        readonly=True,
    )

    amount = fields.Float(string="Amount", readonly=True)
    income_type = fields.Selection(
        [("share", "Share"), ("referral", "Referral")],
        string="Income Type",
        readonly=True,
    )
    visit_date = fields.Date(string="Visit Date", readonly=True)

    fee_share_type = fields.Selection(
        [
            ("percent", "Percentage"),
            ("fixed", "Fixed Amount"),
        ],
        string="Share Type",
        readonly=True,
    )
    fee_share_value = fields.Float(string="Share Value", readonly=True)
    fee_calculation_type = fields.Selection(
        [
            ("actual_price", "Actual Price"),
            ("dicounted_price", "Discounted Subtotal Price"),
            ("dicounted_total_price", "Discounted Total Price"),
        ],
        string="Calculation Type",
        readonly=True,
    )
    is_service_done = fields.Boolean(string="Service Done", readonly=True)
    service_done_time = fields.Datetime(string="Service Done Time", readonly=True)
    is_employee = fields.Boolean(string="Is Employee", readonly=True)
    manager_id = fields.Many2one("hr.employee", string="Manager", readonly=True)
    real_payment_status = fields.Selection(
        [
            ("not_paid", "Not Paid"),
            ("paid", "Fully Paid"),
            ("partially_paid", "Partially Paid"),
        ],
        string="Real Payment Status",
        readonly=True,
    )
    order_detail_id = fields.Many2one(
        "his.order_detail",
        string="Order Detail",
        readonly=True,
    )
    type_visit = fields.Selection(
        [("1", "1П"), ("follow_up", _('Follow-up')), ("2", "2П")], "Visit Type"
    )
    service_qty = fields.Float(
        string="Service Quantity",
        readonly=True,
    )
    doctor_id = fields.Many2one("hr.employee", string="Doctor", readonly=True)
    price_tax = fields.Float(string="Tax")
    price_subtotal = fields.Float(string="Subtotal")
    #     product_type_id = fields.Selection(
    #         [
    #     ('anesthesia', _('Anesthesia')),
    #     ('blood_com', _('Blood components')),
    #     ('consultation', _('Consultation')),
    #     ('dentistry', _('Dentistry')),
    #     ('der_and_cos', _('Dermatology and Cosmetology')),
    #     ('diet', _('Diet')),
    #     ('drug', _('Drug')),
    #     ('functional_exam', _('Functional Examination')),
    #     ('lab_exam', _('Laboratory Examination')),
    #     ('material', _('Material')),
    #     ('medical_product', _('Medical Product')),
    #     ('nutrition', _('Nutrition')),
    #     ('operation', _('Operation')),
    #     ('proc_and_tre', _('Procedures and treatments')),
    #     ('radiology', _('Radiology')),
    #     ('rehabilitation', _('Rehabilitation')),
    #     ('stationary', _('Stationary')),
    #     ('trichology', _('Trichology')),
    #     ('treatment', _('Treatment'))
    # ]
    #     )
    covered_by = fields.Many2one("res.partner", string="Covered By")
    coverer_type = fields.Selection(
        [
            ("patient", _("Patient")),
            ("дмс", _("ДМС")),
            ("b2b", _("B2B")),
            ("state_payer", _("State fund")),
        ],
        string="Coverer Type",
        help="Type of coverer for the service",
        readonly=True,
    )


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    dsb.id,
                    dsb.partner_id,
                    pv.patient_type AS visit_patient_type,
                    pv.patient_id,
                    pv.company_id,
                    so.currency_id,
                    CONCAT(
                        TO_CHAR(psv.date, 'YYYY-MM-DD'), ' ',
                        psv.start_time, ' - ', psv.end_time
                    ) AS scheduled_date_time,
                    sol.price_total,
                    sol.price_unit,
                    sol.product_id AS service_id,
                    sol.price_subtotal,
                    sol.price_tax,
                    sol.covered_by,
                    sol.product_uom_qty AS service_qty,
                    sol.coverer_type,
                    dsb.amount,
                    dsb.income_type,
                    pv.date AS visit_date,
                    dsb.fee_share_type,
                    dsb.fee_share_value,
                    dsb.fee_calculation_type,
                    sol.order_detail_id,
                    od.is_done AS is_service_done,
                    od.done_date AS service_done_time,
                    partner.employee AS is_employee,
                    partner.manager_id,
                    sol.real_payment_state AS real_payment_status,
                    psv.doctor_id,
                    psv.type_visit
                FROM
                    his_doctor_share_and_bonus dsb
                JOIN
                    sale_order_line sol ON dsb.sale_order_line_id = sol.id
                JOIN
                    sale_order so ON sol.order_id = so.id
                JOIN
                    his_order_detail od ON sol.order_detail_id = od.id
                JOIN
                    res_partner partner ON dsb.partner_id = partner.id
                JOIN
                    product_product pp ON sol.product_id = pp.id
                JOIN
                    his_patient_visit pv ON od.patient_visit_id = pv.id
                LEFT JOIN
                    his_patient_visit psv ON od.patient_sub_visit_id = psv.id
            )
        """
            % (self._table)
        )


    def export_to_excel(self):
        # Get filtered records based on active domain (respects tree view filters)
        domain = self._context.get('active_domain', [])
        records = self.search(domain)

        # Check if there are records to export
        if not records:
            raise UserError(_("No data available to export!"))

        # Prepare data for DataFrame
        data = []
        for record in records:
            data.append({
                'Patient': record.patient_id.name or '' if record.patient_id else '',
                'Company': record.company_id.name or '' if record.company_id else '',
                'Service': record.service_id.name or '' if record.service_id else '',
                'Price Total': record.price_total or 0.0,
                'Amount': record.amount or 0.0,
                'Income Type': record.income_type or '',
                'Scheduled Date': record.scheduled_date_time or '',
            })

        # Create DataFrame
        df = pd.DataFrame(data)

        # Add subtotal row for price_total
        total_row = {
            'Patient': '',
            'Company': '',
            'Service': 'Total',
            'Price Total': sum(record.price_total or 0.0 for record in records),
            'Amount': '',
            'Income Type': '',
            'Scheduled Date': '',
        }
        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

        # Create Excel file in memory
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Records', index=False)
            # Adjust column widths for better readability
            worksheet = writer.sheets['Records']
            for col_num, col_name in enumerate(df.columns):
                max_len = max(df[col_name].astype(str).map(len).max(), len(col_name))
                worksheet.set_column(col_num, col_num, max_len)

        # Encode the Excel file
        excel_buffer.seek(0)
        file_data = base64.b64encode(excel_buffer.read())

        # Create attachment
        file_name = f"Records_{fields.Date.today()}.xlsx"
        attachment = self.env['ir.attachment'].sudo().create({
            'name': file_name,
            'type': 'binary',
            'datas': file_data,
            'res_model': self._name,
            'res_id': 0,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }