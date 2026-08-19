from odoo import models, fields, api, exceptions


class ProductBranchConfigurations(models.Model):
    _name = "his.product.branch.conf"
    _description = "Product Branch Configurations"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    service_id = fields.Many2one("product.product", string="Service", required=True)
    product_type_selection = fields.Selection(
        related="service_id.product_type_selection", readonly=True
    )
    base_price = fields.Float(
        string="Base Price", related="service_id.list_price", readonly=True
    )
    base_service_duration = fields.Integer(
        string="Base Service Duration",
        related="service_id.base_service_duration",
        readonly=True,
    )
    base_share_type = fields.Selection(
        related="service_id.base_share_type", readonly=True
    )
    base_share_value = fields.Float(
        related="service_id.base_share_value", readonly=True
    )
    # base_w = fields.Selection(related='service_id.base_recommendation_bonus_type', readonly=True)
    # base_recommendation_bonus_value = fields.Float(related='service_id.base_recommendation_bonus_value', readonly=True)
    service_doctors = fields.One2many(
        "his.doctor_fee", "branch_conf_id", string="Doctor Price & Service Duration"
    )
    schedule_type = fields.Selection(
        string="Is In Queue", related="service_id.schedule_type", readonly=True
    )
    in_queue_doctor_id = fields.Many2one(
        "hr.employee", string="Default In Queue Doctor"
    )

    _sql_constraints = [
        (
            "unique_company_service",
            "unique(company_id, service_id)",
            "The service must be unique per branch!",
        ),
    ]

    doctors_count = fields.Integer(compute="_compute_doctors_count")

    in_queue_doctor_list = fields.Binary(
        string="Queue Doctor Dynamic domain", compute="_compute_dynamic_domain"
    )

    @api.depends("service_doctors")
    def _compute_dynamic_domain(self):
        for record in self:
            virtual_doctor_id = record.service_doctors.filtered(
                lambda r: r.doctor_id.is_virtual
                == True
                # and record.company_id.id in r.doctor_id.user_id.company_ids.ids
            )

            if len(virtual_doctor_id) > 0:
                record.in_queue_doctor_list = [
                    ("id", "in", virtual_doctor_id.mapped("doctor_id").ids)
                ]
                if len(record.service_doctors) == 1 and len(virtual_doctor_id) == 1:
                    record.in_queue_doctor_id = virtual_doctor_id.doctor_id.id
            else:
                record.in_queue_doctor_list = [
                    ("id", "in", record.service_doctors.mapped("doctor_id").ids)
                ]

    @api.depends("service_doctors")
    def _compute_doctors_count(self):
        for rec in self:
            rec.doctors_count = len(rec.service_doctors)
