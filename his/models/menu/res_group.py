from odoo import fields, models


class ResGroups(models.Model):
    _inherit = "res.groups"

    excluded_menu_ids = fields.One2many(
        "his.menu.group.exclusion", "group_id", string="Excluded Menus"
    )
