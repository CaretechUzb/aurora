from odoo import models, api

class ResourceResource(models.Model):
    _inherit = "resource.resource"

    @api.model_create_multi
    def create(self, vals):
        for rec in vals:
            if rec.get("company_id") and rec.get("resource_type", False) in ["user", False]:
                rec["company_id"] = False
        return super(ResourceResource, self).create(vals)
