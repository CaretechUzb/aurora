from odoo import exceptions, fields, models, api, _
from ...utils.selections import categ_selection


class ProductType(models.Model):
    _name = "his.category_base"
    _description = "Product Type Records"
    _order = "sequence, name"

    name = fields.Char(string="Name", translate=True)
    # short_name = fields.Char(string='Short Name', unique=True)
    icon = fields.Binary("Icon")
    category_selection = fields.Selection(
        categ_selection,
        "Category",
        index=True,
    )
    product_definition = fields.PropertiesDefinition("ProductDefinition")
    share_type = fields.Selection(
        [
            ("percent", "Percentage"),
            ("fixed", "Fixed Amount"),
        ],
        string="Share Type",
        default="percent",
    )
    share_value = fields.Float(string="Share Value")
    recommendation_bonus_type = fields.Selection(
        [
            ("percent", "Percentage"),
            ("fixed", "Fixed Amount"),
        ],
        string="Recomendation Bonus Type",
        default="percent",
    )
    recommendation_bonus_value = fields.Float(string="Recomendation Bonus Value")
    is_schedulable = fields.Boolean("Is Schdedulable")
    schedule_type = fields.Selection(
        [
            ("default", "Default"),
            ("in_queue", "In Queue"),
        ],
        default="default",
    )

    can_online_appointment = fields.Boolean()
    can_receive_call_back = fields.Boolean()
    sorting_to_website = fields.Integer("Sorting to Show in Website")
    product_ids = fields.One2many("product.product", "product_type")

    available_in_registration = fields.Boolean(
        string="Available in Registration",
        tracking=True,
        default=True,
    )
    sequence = fields.Integer(
        string="Sequence",
        default=0,
        help="Gives the sequence order when displaying a list of product types.",
    )

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        ctx = self._context
        order_list = []
        if order:
            order_list.append(order)
        if "order_display" in ctx:
            order_list.append(ctx["order_display"])
        order = ", ".join(order_list)
        res = super(ProductType, self)._search(
            args, offset=offset, limit=limit, order=order, count=count
        )
        return res

    def manage_product_website_fields(self):
        self.mapped("product_ids").sudo().write(
            {
                "can_online_appointment": self.can_online_appointment,
                "can_receive_call_back": self.can_receive_call_back,
            }
        )
        categories = self.mapped("product_ids.categ_id")
        categories.sudo().write(
            {
                "can_online_appointment": self.can_online_appointment,
            }
        )
