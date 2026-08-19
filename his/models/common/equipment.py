from odoo import _, models, fields, tools


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    is_his = fields.Boolean(string="Is HIS", default=False)
    room_id = fields.Many2one("his.room", string="Room", check_company=True)
