# -*- coding: utf-8 -*-
from random import randint

from odoo import api, fields, models, _
from odoo.osv import expression


class ProductNNM(models.Model):
    _name = "product.nnm"
    _description = "Product NNM"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char("Name", required=True, translate=True)
    color = fields.Integer("Color", default=_get_default_color)

    product_template_ids = fields.Many2many(
        "product.template", "product_nnm_product_template_rel"
    )
    product_product_ids = fields.Many2many(
        "product.product", "product_nnm_product_product_rel"
    )
    product_ids = fields.Many2many(
        "product.product",
        string="All Product Variants using this NNM",
        compute="_compute_product_ids",
        search="_search_product_ids",
    )
    snomed_id = fields.Many2one(
        "his.snomed",
        string="SNOMED CT Code",
        tracking=True,
        help="SNOMED CT code for this product/medicine (used in DHP FHIR sync)",
    )

    _sql_constraints = [
        ("name_uniq", "unique (name)", _("Name already exists !")),
    ]

    @api.depends("product_template_ids", "product_product_ids")
    def _compute_product_ids(self):
        for nnm in self:
            nnm.product_ids = (
                nnm.product_template_ids.product_variant_ids | nnm.product_product_ids
            )

    def _search_product_ids(self, operator, operand):
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            return [
                ("product_template_ids.product_variant_ids", operator, operand),
                ("product_product_ids", operator, operand),
            ]
        return [
            "|",
            ("product_template_ids.product_variant_ids", operator, operand),
            ("product_product_ids", operator, operand),
        ]
