from odoo import fields, models


class MenuGroupExclusion(models.Model):
    _name = "his.menu.group.exclusion"
    _description = "Menu group exclusion mapping"

    menu_xml_id = fields.Char("Menu xml Id", required=True)
    group_id = fields.Many2one("res.groups", "Group", required=True)
