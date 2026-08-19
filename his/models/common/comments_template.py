from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class CommentsTemplate(models.Model):
    _name = "his.comments_template"
    _description = "Comments Template Records"
    _rec_name = "name"

    type = fields.Selection(
        [
            ("dept", "Department"),
            ("person", "Person"),
        ],
        string="Type",
        default="dept",
        required=True,
    )
    name = fields.Char(string="Name", required=True)
    comment = fields.Text(string="Comment", required=True)
    department_id = fields.Many2one("hr.department", string="Department")

    @api.model
    def create(self, vals_list):
        if vals_list.get("type") == "dept" and not vals_list.get("department_id"):
            raise ValidationError(_("Department is required for department type"))
        elif vals_list.get("type") == "person" and vals_list.get("department_id"):
            raise ValidationError(_("Department is not required for person type"))
        return super(CommentsTemplate, self).create(vals_list)
