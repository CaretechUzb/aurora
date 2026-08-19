# -*- coding: utf-8 -*-
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        info = super().session_info()
        user = self.env.user
        if not user.action_id:
            employee = (
                self.env["hr.employee"]
                .sudo()
                .search([("user_id", "=", user.id)], limit=1)
            )
            if employee and employee.job_id and employee.job_id.action_id:
                info["home_action_id"] = employee.job_id.action_id.id
        return info
