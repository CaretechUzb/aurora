from odoo import models, fields


class PrescriptionTemplate(models.Model):
    _name = "his.prescription_template"
    _description = "Prescription Template Records"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    name = fields.Char(string="Name", translate=True)
    department_id = fields.Many2one(
        "hr.department", string="Department", check_company=True
    )
    employee_id = fields.Many2one("hr.employee", string="Employee", check_company=True)
    services = fields.Many2many(
        "product.product", string="Services", check_company=True
    )
    diagnosis = fields.Many2many("his.diagnosis", string="Diagnosis")
