from ...utils.selections import categ_selection
from odoo import models, fields, api, _


class ProductCategory(models.Model):
    _inherit = "product.category"
    _rec_name = 'name'

    name = fields.Char(translate=True)

    # short_name = fields.Char(string='Short Name', unique=True)
    description = fields.Text("Description", translate=True)
    icon = fields.Binary("Icon")
    is_his = fields.Boolean(string="Is HIS")
    is_lis_category = fields.Boolean(string="Is LIS Category")
    share_type = fields.Selection(
        [
            ("percent", "Percentage"),
            ("fixed", "Fixed Amount"),
        ],
        string="Share Type",
        default="percent",
    )
    share_value = fields.Float(string="Share Value")
    # recommendation_bonus_type = fields.Selection(
    #     [
    #         ("percent", "Percentage"),
    #         ("fixed", "Fixed Amount"),
    #     ],
    #     string="Recomendation Bonus Type",
    #     default="percent",
    # )
    # recommendation_bonus_value = fields.Float(string="Recomendation Bonus Value")
    is_schedulable = fields.Boolean("Is Schdedulable")
    schedule_type = fields.Selection(
        [
            ("default", "Default"),
            ("in_queue", "In Queue"),
        ],
        default="default",
    )

    employee_ids = fields.Many2many(
        "hr.employee",
        "hr_employee_product_category_rel",
        column1="product_category_id",
        column2="hr_employee_id",
        string="Doctors",
    )
    no_virtual_employee_count = fields.Integer(
        string="Employee count",
        compute="_compute_no_virtual_employee_count",
        store=True,
    )

    can_online_appointment = fields.Boolean()
    # can_receive_call_back = fields.Boolean()
    product_ids = fields.One2many("product.product", "categ_id")
    sorting = fields.Integer("Sorting")
    sequence = fields.Integer(
        string="Sequence",
        default=0,
        help="Gives the sequence order when displaying a list of product categories.",
    )

    available_in_registration = fields.Boolean(
        string="Available in Registration",
        tracking=True,
        default=True,
    )

    @api.depends("employee_ids")
    def _compute_no_virtual_employee_count(self):
        for rec in self:
            rec.no_virtual_employee_count = len(
                rec.employee_ids.filtered(lambda x: x.is_virtual == False)
            )

    # @api.onchange('product_type')
    # def onchange_product_type(self):
    #     if self.product_type:
    #         self.share_type = self.product_type.share_type
    #         self.share_value = self.product_type.share_value
    #         self.recommendation_bonus_type = self.product_type.recommendation_bonus_type
    #         self.recommendation_bonus_value = self.product_type.recommendation_bonus_value


class ProductCategoryWithBaseView(models.Model):
    _name = "his.category_with_base.view"
    _description = "Product Category With Base View"
    _auto = False
    _order = "sequence, name"

    name = fields.Char(string="Name", translate=True)
    parent_id = fields.Many2one("product.category", string="Parent Category")
    is_his = fields.Boolean(string="Is HIS")
    product_type = fields.Char(string="Product Type")
    available_in_registration = fields.Boolean(
        string="Available in Registration",
    )
    sequence = fields.Integer(string="Sequence")

    def init(self):
        # Use tools.sql.drop_view_if_exists to safely drop the view if it already exists
        self.env.cr.execute("""DROP VIEW IF EXISTS his_category_with_base_view""")
        self.env.cr.execute(
            """
            CREATE VIEW his_category_with_base_view AS (
               SELECT DISTINCT
                pc.id,
                pc.name,
                pc.parent_id,
                pc.is_his,
                pc.sequence,
                pc.available_in_registration,
                array_agg(DISTINCT pt.product_type) as product_type
            FROM
                product_category pc inner join product_template pt on pc.id = pt.categ_id
            group by pc.id, pc.name, pc.parent_id, pc.is_his, pc.sequence
            )
        """
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
            order_list.insert(0, ctx["order_display"])
        order = ", ".join(order_list)
        res = super(ProductCategoryWithBaseView, self)._search(
            args, offset=offset, limit=limit, order=order, count=count
        )
        return res

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        for arg in args:
            if arg[0] == "product_type" and arg[1] == "ilike":
                product_type_filter = arg[2]
                self.env.cr.execute(
                    """
                    SELECT id
                    FROM his_category_with_base_view
                    WHERE array_to_string(product_type, ',') ILIKE %s
                """,
                    ("%" + product_type_filter + "%",),
                )
                ids = [row[0] for row in self.env.cr.fetchall()]
                args.append(("id", "in", ids))
                args.remove(arg)

        return super(ProductCategoryWithBaseView, self).search(
            args, offset, limit, order, count
        )
