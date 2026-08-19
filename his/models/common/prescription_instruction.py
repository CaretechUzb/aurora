from odoo import models, fields


class PrescriptionInstruction(models.Model):
    _name = "his.prescription_instruction"
    _description = "Prescription Instruction"
    _rec_name = "instruction"

    instruction = fields.Char(string="Instruction", translate=True)
    code = fields.Char(string="Code")
    times = fields.Integer(string="Times")
