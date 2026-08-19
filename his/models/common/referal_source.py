import re

from odoo import fields, models, api, _
from odoo.osv import expression
from odoo.addons.his.utils.cyrillic_latin_translator import to_latin, to_cyrillic
from odoo.addons.his.utils.name_utils import capitalize_name


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    referral_is_required = fields.Boolean(string="Referral Source Setting")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            referral_is_required=self.env["ir.config_parameter"]
            .sudo()
            .get_param("referral_is_required", default=False)
        )
        return res

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "referral_is_required", self.referral_is_required
        )


class ReferralSourceByService(models.Model):
    _name = "his.referral_source_by_service"
    _description = "Referral Source by Service"

    partner_id = fields.Many2one("res.partner", string="Partner", index=True, ondelete="cascade")
    product_category_id = fields.Many2one("product.category", string="Product Category", index=True)
    service_id = fields.Many2one("product.product", string="Service", index=True)
    referral_bonus_type = fields.Selection(
        [
            ("percent", "Percentage"),
            ("fixed", "Fixed Amount"),
            ("formula", "Formula"),
        ],
        string="Referral Bonus Type",
        default="percent",
    )
    referral_bonus_value = fields.Float(string="Referral Bonus Value")
    internal_formula = fields.Char(
        string="Internal Formula",
        help="Python formula for internal (employee) referrals. Variables: price_subtotal, discount_total, price_total, quantity, price_tax, price, actual_price"
    )
    external_formula = fields.Char(
        string="External Formula",
        help="Python formula for external (non-employee) referrals. Variables: price_subtotal, discount_total, price_total, quantity, price_tax, price, actual_price"
    )
    calculation_type = fields.Selection(
        [
            ("actual_price", "Actual Price"),
            ("dicounted_price", "Discounted Subtotal Price"),
            ("dicounted_total_price", "Discounted Total Price"),
        ],
        string="Calculation Type",
        default="dicounted_price",
    )

    internal_amount = fields.Float(string="Internal Amount")
    external_amount = fields.Float(string="External Amount")

    @api.onchange("referral_bonus_value")
    def _onchange_referral_bonus_value(self):
        if self.referral_bonus_value or self.referral_bonus_value == 0.0:
            self.internal_amount = self.referral_bonus_value
            self.external_amount = self.referral_bonus_value

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, f"{record.service_id.name} - {record.referral_bonus_value}")
            )
        return result

    @api.model
    def _update_existing_records_in_batches(self, batch_size=5000):
        batch_size = batch_size
        all_records = self.search([], order="id asc")
        for i in range(0, len(all_records), batch_size):
            batch = all_records[i : i + batch_size]
            self.with_delay()._process_batch(batch.ids)

    def _process_batch(self, record_ids):
        """Splits records into batches of 5000 and creates a separate job for each batch. service"""
        records = self.browse(record_ids)
        for rec in records:
            if rec.internal_amount == 0.0:
                rec.internal_amount = rec.referral_bonus_value
            if rec.external_amount == 0.0:
                rec.external_amount = rec.referral_bonus_value


class ReferralSourceByProductType(models.Model):
    _name = "his.referral_source_by_product_type"
    _description = "Referral Source by Product Type"

    partner_id = fields.Many2one("res.partner", string="Partner", ondelete="cascade")
    product_type_id = fields.Many2one("his.category_base", string="Product type")
    referral_bonus_type = fields.Selection(
        [
            ("percent", "Percentage"),
            ("fixed", "Fixed Amount"),
            ("formula", "Formula"),
        ],
        string="Referral Bonus Type",
        default="percent",
    )
    referral_bonus_value = fields.Float(string="Referral Bonus Value")
    internal_formula = fields.Char(
        string="Internal Formula",
        help="Python formula for internal (employee) referrals. Variables: price_subtotal, discount_total, price_total, quantity, price_tax, price, actual_price"
    )
    external_formula = fields.Char(
        string="External Formula",
        help="Python formula for external (non-employee) referrals. Variables: price_subtotal, discount_total, price_total, quantity, price_tax, price, actual_price"
    )
    calculation_type = fields.Selection(
        [
            ("actual_price", "Actual Price"),
            ("dicounted_price", "Discounted Subtotal Price"),
            ("dicounted_total_price", "Discounted Total Price"),
        ],
        string="Calculation Type",
        default="dicounted_price",
    )
    internal_amount = fields.Float(string="Internal Amount")
    external_amount = fields.Float(string="External Amount")

    @api.onchange("referral_bonus_value")
    def _onchange_referral_bonus_value(self):
        if self.referral_bonus_value or self.referral_bonus_value == 0.0:
            self.internal_amount = self.referral_bonus_value
            self.external_amount = self.referral_bonus_value

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (
                    record.id,
                    f"{record.product_type_id.name} - {record.referral_bonus_value}",
                )
            )
        return result

    @api.model
    def _update_existing_records_in_batches(self, batch_size=5000):
        batch_size = batch_size
        all_records = self.search([], order="id asc")
        for i in range(0, len(all_records), batch_size):
            batch = all_records[i : i + batch_size]
            self.with_delay()._process_batch(batch.ids)

    def _process_batch(self, record_ids):
        """Splits records into batches of 5000 and creates a separate job for each batch. product type"""
        records = self.browse(record_ids)
        for rec in records:
            if rec.internal_amount == 0.0:
                rec.internal_amount = rec.referral_bonus_value
            if rec.external_amount == 0.0:
                rec.external_amount = rec.referral_bonus_value


class ReferralSourceByProductCategory(models.Model):
    _name = "his.referral_source_by_product_category"
    _description = "Referral Source by Product Category"

    partner_id = fields.Many2one("res.partner", string="Partner", index=True, ondelete="cascade")
    product_category_id = fields.Many2one(
        "product.category", string="Product Category", index=True
    )
    referral_bonus_type = fields.Selection(
        [
            ("percent", "Percentage"),
            ("fixed", "Fixed Amount"),
            ("formula", "Formula"),
        ],
        string="Referral Bonus Type",
        default="percent",
    )
    referral_bonus_value = fields.Float(string="Referral Bonus Value")
    internal_formula = fields.Char(
        string="Internal Formula",
        help="Python formula for internal (employee) referrals. Variables: price_subtotal, discount_total, price_total, quantity, price_tax, price, actual_price"
    )
    external_formula = fields.Char(
        string="External Formula",
        help="Python formula for external (non-employee) referrals. Variables: price_subtotal, discount_total, price_total, quantity, price_tax, price, actual_price"
    )
    calculation_type = fields.Selection(
        [
            ("actual_price", "Actual Price"),
            ("dicounted_price", "Discounted Subtotal Price"),
            ("dicounted_total_price", "Discounted Total Price"),
        ],
        string="Calculation Type",
        default="dicounted_price",
    )
    internal_amount = fields.Float(string="Internal Amount")
    external_amount = fields.Float(string="External Amount")

    @api.onchange("referral_bonus_value")
    def _onchange_referral_bonus_value(self):
        if self.referral_bonus_value or self.referral_bonus_value == 0.0:
            self.internal_amount = self.referral_bonus_value
            self.external_amount = self.referral_bonus_value

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (
                    record.id,
                    f"{record.product_category_id.name or _('(no category)')} - {record.referral_bonus_value}",
                )
            )
        return result

    @api.model
    def _update_existing_records_in_batches(self, batch_size=5000):
        batch_size = batch_size
        all_records = self.search([], order="id asc")
        for i in range(0, len(all_records), batch_size):
            batch = all_records[i : i + batch_size]
            self.with_delay()._process_batch(batch.ids)

    def _process_batch(self, record_ids):
        """Splits records into batches of 5000 and creates a separate job for each batch. product category"""
        records = self.browse(record_ids)
        for rec in records:
            if rec.internal_amount == 0.0:
                rec.internal_amount = rec.referral_bonus_value
            if rec.external_amount == 0.0:
                rec.external_amount = rec.referral_bonus_value


class ReferralSource(models.Model):
    _inherit = "res.partner"
    # for name searching
    # _rec_names_search = ['display_name', 'email', 'ref', 'vat', 'company_registry']  # TODO vat must be sanitized the same way for storing/searching

    code = fields.Char(string="code")

    first_name = fields.Char(string="First name", tracking=True)
    middle_name = fields.Char(string="Middle name", tracking=True)
    last_name = fields.Char(string="Last name", tracking=True)
    # full_name = fields.Char(
    #     string="Full Name", compute="_compute_full_name"
    # )

    is_patient = fields.Boolean()

    state_id = fields.Many2one(
        "res.country.state", string=_("State"), ondelete="restrict"
    )
    district_id = fields.Many2one("res.state.district", string=_("District"))

    manager_id = fields.Many2one("hr.employee", string="Manager ")
    created_date = fields.Date(
        string="Created Date", default=lambda self: fields.Date.context_today(self)
    )
    card_num = fields.Char("Plastic Card number", tracking=True)

    has_bonus = fields.Boolean(string="Has Bonus", default=False)

    # product_type_id = fields.Many2many('his.category_base', string='Product Type')

    referral_bonus_type = fields.Selection(
        [
            ("percent", "Percentage"),
            ("fixed", "Fixed Amount"),
            ("formula", "Formula"),
        ],
        string="Referral Bonus Type",
        default="percent",
    )
    referral_bonus_value = fields.Float(string="Referral Bonus Value")
    formula = fields.Char(string="Formula", help="Python formula to calculate referral bonus. Available variables: price_subtotal, discount_total, price_total, quantity, price_tax, price, actual_price")
    calculation_type = fields.Selection(
        [
            ("actual_price", "Actual Price"),
            ("dicounted_price", "Discounted Subtotal Price"),
            ("dicounted_total_price", "Discounted Total Price"),
        ],
        string="Calculation Type",
        default="dicounted_price",
    )

    referral_count = fields.Integer(
        compute="_compute_referral_info", string="Referral Count", store=True
    )
    total_earnings = fields.Float(
        compute="_compute_referral_info", string="Total Earnings", store=True
    )

    referral_source_by_service_ids = fields.One2many(
        "his.referral_source_by_service",
        "partner_id",
        string="Referral Source By Service",
    )
    referral_source_by_product_type_ids = fields.One2many(
        "his.referral_source_by_product_type",
        "partner_id",
        string="Referral Source By Product Type",
    )
    referral_source_by_product_category_ids = fields.One2many(
        "his.referral_source_by_product_category",
        "partner_id",
        string="Referral Source By Product Category",
    )

    earned_referral_ids = fields.One2many(
        "his.doctor_share_and_bonus", "partner_id", string="Earned Referrals"
    )
    stir = fields.Integer(string="STIR", help=_("Bank STIR"))
    deposit_amount_before_refund = fields.Float(
        string="Amount before refund",
        help=_("Only write last deposit amount before last refund"),
    )

    commercial_company_name = fields.Char(
        "Company Name Entity",
        compute="_compute_commercial_company_name",
        inverse="_inverse_commercial_company_name",
        store=True,
    )

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}

        if self.referral_source_by_service_ids:
            default["referral_source_by_service_ids"] = [
                (0, 0, rec.copy_data()[0])
                for rec in self.referral_source_by_service_ids
            ]

        if self.referral_source_by_product_type_ids:
            default["referral_source_by_product_type_ids"] = [
                (0, 0, rec.copy_data()[0])
                for rec in self.referral_source_by_product_type_ids
            ]

        if self.referral_source_by_product_category_ids:
            default["referral_source_by_product_category_ids"] = [
                (0, 0, rec.copy_data()[0])
                for rec in self.referral_source_by_product_category_ids
            ]

        return super(ReferralSource, self).copy(default)

    def _inverse_commercial_company_name(self):
        for partner in self:
            partner.company_name = partner.commercial_company_name

    @api.depends("company_name", "parent_id.is_company", "commercial_partner_id.name")
    def _compute_commercial_company_name(self):
        for partner in self:
            if not partner.commercial_company_name:
                p = partner.commercial_partner_id
                partner.commercial_company_name = (
                    p.is_company and p.name or partner.company_name
                )

    @api.model
    def _get_referral_info_map(self, partner_ids):
        if not partner_ids:
            return {}

        results = self.env["his.doctor_share_and_bonus"].read_group(
            domain=[("partner_id", "in", partner_ids), ("income_type", "=", "referral")],
            fields=["partner_id", "amount"],
            groupby=["partner_id"],
        )
        return {
            row["partner_id"][0]: (row["partner_id_count"], row["amount"])
            for row in results
        }

    @api.depends("earned_referral_ids.amount", "earned_referral_ids.income_type")
    def _compute_referral_info(self):
        if not self.ids:
            for record in self:
                record.referral_count = 0
                record.total_earnings = 0.0
            return

        mapped = self._get_referral_info_map(self.ids)
        for record in self:
            count, total = mapped.get(record.id, (0, 0.0))
            record.referral_count = count
            record.total_earnings = total

    @api.model
    def enqueue_compute_referral_info(self, partner_ids=None, batch_size=100):
        partner_ids = partner_ids or self.search([]).ids
        if not partner_ids:
            return

        for i in range(0, len(partner_ids), batch_size):
            batch_ids = partner_ids[i : i + batch_size]
            self.with_delay()._compute_referral_info_batch(batch_ids)

    def _compute_referral_info_batch(self, partner_ids):
        partners = self.browse(partner_ids).exists()
        if not partners:
            return

        mapped = self._get_referral_info_map(partners.ids)
        for partner in partners:
            count, total = mapped.get(partner.id, (0, 0.0))
            partner.write(
                {
                    "referral_count": count,
                    "total_earnings": total,
                }
            )

    # @api.depends("middle_name", "last_name", "first_name")
    # def _compute_full_name(self):
    #     for record in self:
    #         names = [record.last_name, record.first_name, record.middle_name]
    #         record.name = " ".join(filter(None, names)) or record.name
    #         record.full_name = record.name

    @api.onchange("first_name", "last_name", "middle_name")
    def _onchange_referral_name(self):
        if self.first_name:
            self.first_name = capitalize_name(self.first_name)
        if self.last_name:
            self.last_name = capitalize_name(self.last_name)
        if self.middle_name:
            self.middle_name = capitalize_name(self.middle_name)
        name_parts = [self.last_name, self.first_name, self.middle_name]
        self.name = " ".join(filter(None, name_parts)) or self.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            for field in ("first_name", "last_name", "middle_name"):
                if vals.get(field):
                    vals[field] = capitalize_name(vals[field])
            name_parts = [vals.get("last_name"), vals.get("first_name"), vals.get("middle_name")]
            name_parts = [part for part in name_parts if part]
            if name_parts:
                vals["name"] = " ".join(name_parts)

        return super(ReferralSource, self).create(vals_list)

    def write(self, vals):
        for field in ("first_name", "last_name", "middle_name"):
            if vals.get(field):
                vals[field] = capitalize_name(vals[field])
        name_fields = {'first_name', 'last_name', 'middle_name'}
        if name_fields.intersection(vals):
            for record in self:
                first_name = vals.get('first_name', record.first_name)
                last_name = vals.get('last_name', record.last_name)
                middle_name = vals.get('middle_name', record.middle_name)
                name_parts = [part for part in [last_name, first_name, middle_name] if part]
                if name_parts:
                    record_vals = vals.copy()
                    record_vals['name'] = ' '.join(name_parts)
                    super(ReferralSource, record).write(record_vals)
                else:
                    super(ReferralSource, record).write(vals)
            return True
        return super(ReferralSource, self).write(vals)

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

        search_more_name = ctx.get("search_more_name")
        search_more_similarity = bool(
            ctx.get("search_more_similarity") and search_more_name and not count
        )
        id_in_filter_ids = None
        if search_more_similarity and args:
            for arg in args:
                if (
                    isinstance(arg, (tuple, list))
                    and len(arg) >= 3
                    and arg[0] == "id"
                    and arg[1] == "in"
                    and isinstance(arg[2], (list, tuple))
                ):
                    id_in_filter_ids = arg[2]
                    break

        if (
            search_more_similarity
            and id_in_filter_ids is not None
            and len(id_in_filter_ids) <= 1000
        ):
            all_ids = super(ReferralSource, self)._search(
                args, offset=0, limit=None, order=order, count=False
            )
            if not all_ids:
                return all_ids
            ordered_ids = self.browse(all_ids)._order_by_name_similarity(
                search_more_name
            ).ids
            if offset:
                ordered_ids = ordered_ids[offset:]
            if limit is not None:
                ordered_ids = ordered_ids[:limit]
            return ordered_ids

        res = super(ReferralSource, self)._search(
            args, offset=offset, limit=limit, order=order, count=count
        )

        return res

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=1000):
        if args is None:
            args = []
        if name.isdigit():
            if 1 <= int(name) <= 2147483647:
                digit_domain = [
                    "|",
                    "&",
                    ("id", "=", int(name)),
                    ("code", "=", False),
                    "&",
                    ("code", "=", name),
                    ("code", "!=", False),
                ]
                args = digit_domain + args
            return self._search(args, limit=limit)

        elif name and name[0] == '+':
            name = name[1:]
            args = [("phone", "ilike", name)] + args
            return self._search(args, limit=limit)

        else:
            name_tokens = [token for token in re.split(r"\s+", (name or "").strip()) if token]
            token_domains = []
            for token in name_tokens:
                token_domains.append(
                    [
                        "|",
                        ("name", operator, to_cyrillic(token)),
                        ("name", operator, to_latin(token)),
                    ]
                )
            if token_domains:
                args = expression.AND([args, expression.AND(token_domains)])
            self.env.cr.execute("SELECT set_limit(0.3);")

        ids = self._search(args, limit=limit)
        if name and ids:
            return self.browse(ids)._order_by_name_similarity(name).ids
        return ids

    def _order_by_name_similarity(self, name):
        if not self or not name:
            return self
        name = name.strip()
        if not name:
            return self

        name_cyr = to_cyrillic(name)
        name_lat = to_latin(name)

        tokens = []
        for raw in (name, name_cyr, name_lat):
            for part in re.split(r"\s+", raw.strip()):
                if part:
                    tokens.append(part.lower())
        if not tokens:
            return self

        seen = set()
        uniq_tokens = []
        for token in tokens:
            if token not in seen:
                seen.add(token)
                uniq_tokens.append(token)

        def score_expr_name():
            parts = []
            for _ in uniq_tokens:
                parts.append(
                    """
                    CASE
                        WHEN lower(coalesce(name, '')) LIKE %s
                             OR lower(coalesce(name, '')) LIKE %s
                        THEN 5
                        WHEN lower(coalesce(name, '')) LIKE %s
                        THEN 1
                        ELSE 0
                    END
                    """
                )
            return " + ".join(parts) if parts else "0"

        score_sql = f"({score_expr_name()})"
        score_params = []
        for token in uniq_tokens:
            score_params.extend([f"{token}%", f"% {token}%", f"%{token}%"])

        params = score_params + [name, name_cyr, name_lat, self.ids]
        self.env.cr.execute(
            f"""
            SELECT id,
                   {score_sql} AS score,
                   GREATEST(
                       similarity(lower(coalesce(name, '')), lower(%s)),
                       similarity(lower(coalesce(name, '')), lower(%s)),
                       similarity(lower(coalesce(name, '')), lower(%s))
                   ) AS sim
            FROM {self._table}
            WHERE id = ANY(%s)
            ORDER BY score DESC, sim DESC, id DESC
            """,
            tuple(params),
        )
        ids = [row[0] for row in self.env.cr.fetchall()]
        return self.browse(ids)

    def name_get(self):
        result = []
        for rec in self:
            if rec.name:
                clean_name = " ".join(
                    sentence
                    for sentence in rec.name.split(" ")
                    if not sentence.isdigit()
                )
                id = rec.id
                if rec.code:
                    id = rec.code
                result.append((rec.id, f"{id} {clean_name}"))
        return result
