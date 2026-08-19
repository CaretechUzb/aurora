from ...utils.selections import categ_selection
from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    description = fields.Html(
        'Description', translate=True, sanitize=False)
    product_type = fields.Many2one("his.category_base", string="Category Base")
    product_type_selection = fields.Selection(
        related="product_type.category_selection", string="Product Type Selection"
    )
    medical_classification_type = fields.Selection(
        [
            ("normal", "Normal"),
            ("psychotropic", "Psychotropic"),
            ("narcotic", "Narcotic"),
            ("antimicrobial", "Antimicrobial"),
            ("limited_antimicrobial", "Limited Antimicrobial"),
            ("tpn", "Limited Antimicrobial"),
            ("contrast_medium", "Contrast Medium"),
            ("raw_materials_medicine", "Raw Materials Medicine"),
            ("anticancer_medicine", "Anticancer Medium"),
            ("sap", "Sap"),
        ],
        "Medical Classification Type",
    )
    categ_is_his = fields.Boolean(
        string="Is HIS", related="categ_id.is_his", store=True
    )
    list_price = fields.Float(tracking=True)

    tx_meds = fields.Selection([("yes", "Yes"), ("no", "No")], "Tx Meds")
    age = fields.Selection(
        [("all", "All"), ("child", "Child"), ("adult", "Adult")],
        "Age",
        default="all",
        required=True,
    )
    rx_out_host = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        "Rx Out Hosp",
    )
    instruction = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        "Product Instruction",
    )
    set_test = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        "Product Set Test",
    )
    from_date = fields.Date()
    to_date = fields.Date()
    # slip_code=

    calculation_type = fields.Selection(
        [
            ("pack", "Pack"),
            ("one_time", "One Time"),
        ],
        string="Calculation Type",
    )
    room_id = fields.Many2one("his.room", string="Room")
    quantity_in_pack = fields.Float(string="Quantity in Pack")
    pack_type_id = fields.Many2one("his.unit_pack_type", string="Pack Type")
    quantity_text = fields.Char(compute="_compute_quantity_text")
    basic_type_id = fields.Many2one("his.unit_pack_type", string="Basic Type")
    basic_price = fields.Integer(string="Basic Price", help="Price for one unit")
    is_rx_possible = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        "Is Rx",
    )
    calc_ext_use_drug = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        "Product Calc Extra Use Drug",
    )
    price_type = fields.Selection(
        [
            ("single", "Single"),
            ("group", "Group"),
        ],
        "Price Type",
    )
    category_service_type = fields.Char(string="Service Type")
    categ_id = fields.Many2one("product.category", string="Category")

    medical_classification_id = fields.Many2one(
        "his.medicine_classification", string="Med Classification"
    )
    med_direction_core = fields.Char(
        string="Med Direction Core",
        related="medical_classification_id.abbreviation",
        store=True,
    )

    product_properties = fields.Properties(
        "Properties", definition="product_type.product_definition"
    )

    basic_dosage = fields.Char(string="Basic Dosage")
    default_no = fields.Char(string="Default No")
    daily_max_amt = fields.Integer(string="Daily Max Amt")
    content = fields.Integer(string="Content")
    amt_unit = fields.Many2one("uom.uom", "Amount Unit of Measure")
    product_nnm_ids = fields.Many2many(
        "product.nnm", "product_nnm_product_template_rel"
    )
    gtin_id = fields.Many2one("his.gtin_products", string="GTIN", tracking=True)

    subtract_from_share_bonus = fields.Boolean(
        string="Subtract from share bonus",
        help="When enabled, the price of pack components will be subtracted from doctor share and referral bonus calculations",
        tracking=True,
    )
    subtract_from_referral_bonus = fields.Boolean(
        string="Subtract from referral bonus",
        help="When enabled, the price of pack components will be subtracted from doctor share and referral bonus calculations",
        tracking=True,
    )

    @api.depends("amt_unit", "content", "uom_id")
    def _compute_quantity_text(self):
        for rec in self:
            if rec.amt_unit and rec.content and rec.uom_id:
                rec.quantity_text = (
                    f"1 {rec.uom_id.name} = {rec.content} {rec.amt_unit.name}"
                )
            else:
                rec.quantity_text = ""

    def action_emr_create(self):
        wizard = self.env["his.patient_visit_emr_create"].create({})
        return {
            "name": _("Create EMR"),
            "type": "ir.actions.act_window",
            "res_model": "his.patient_visit_emr_create",
            "res_id": wizard.id,
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "current",
        }
