from odoo import models, fields, api


class RoomType(models.Model):
    _name = "his.room.type"
    _inherit = "mail.thread"
    _description = "Room Type"

    name = fields.Char(tracking=True)


class Room(models.Model):
    _name = "his.room"
    _inherit = "mail.thread"
    _description = "Room Records"
    _order = "building_number, floor, number"

    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True, tracking=True)
    type = fields.Many2one("his.room.type", string="Room Type", tracking=True)
    title = fields.Char(
        string="Title",
        translate=True,
        compute="_compute_title",
        store=True,
        tracking=True,
    )
    number = fields.Char(string="Number", translate=True, tracking=True)
    category_id = fields.Many2one("product.category", string="Category", tracking=True)
    department_id = fields.Many2one("hr.department", string="Department", tracking=True)
    floor = fields.Integer(string="Floor", required=False, default=1, tracking=True)

    building_number = fields.Integer(string="Building Number", tracking=True)

    @api.depends("floor", "number", "building_number")
    def _compute_title(self):
        for record in self:
            title = ""
            if record.building_number:
                title += f"{record.building_number}-"
            if record.floor and record.number:
                title += f"{record.floor}-{record.number}"

            record.title = title

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, f"{rec.title} {rec.type.name}"))
        return result

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=1000):
        if not args:
            args = []
        if name:
            if "-" in name:
                floor, number = name.split("-")
                args += [("floor", operator, floor), ("number", operator, number)]
            else:
                args += [("title", operator, name)]
        return self._search(args, limit=limit)
