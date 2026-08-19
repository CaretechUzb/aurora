from odoo import exceptions, models, fields, api, _, tools


class SelectedDiagnosis(models.Model):
    _name = "his.selected_diagnosis"
    _description = "Diagnosis Records"

    code = fields.Char(string="Code")
    name = fields.Char(string="Name", translate=True)
    category_id = fields.Many2one("his.diagnosis_category", string="Category")
    type = fields.Selection(
        [
            ("main", "Main"),
            ("admission", "Admission"),
            ("preliminary", "Preliminary"),
            ("referral", "Referral"),
            ("background", "Background"),
            ("concurrent", "Concurrent"),
            ("complications", "Complications"),
            ("related", "Related"),
        ],
        string="Type",
    )

    patient_visit_id = fields.Many2one("his.patient_visit", string="Patient Visit")
    complete_name = fields.Char(
        "Complete Name", compute="_compute_complete_name", store=True
    )

    @api.depends("name", "code")
    def _compute_complete_name(self):
        for rec in self:
            rec.complete_name = "%s (%s)" % (rec.name, rec.code)

    @api.onchange("type")
    def _onchange_type(self):
        if self.type == "main":
            patient_diagnosis = self.search(
                [
                    ("patient_visit_id", "=", self.patient_visit_id.id),
                    ("type", "=", "main"),
                ]
            )
            if patient_diagnosis:
                raise exceptions.ValidationError(
                    _('You can only choose one "Main" diagnosis per visit')
                )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, f"{record.code} - {record.name}"))
        return result


class SelectedDiagnosisView(models.Model):
    """Database view for selected diagnosis with visit-related fields."""
    _name = "his.selected_diagnosis.view"
    _description = "Selected Diagnosis (view)"
    _auto = False

    code = fields.Char(string="Code", readonly=True)
    name = fields.Char(string="Name", readonly=True, translate=True)
    category_id = fields.Many2one(
        "his.diagnosis_category", string="Category", readonly=True
    )
    type = fields.Selection(
        [
            ("main", "Main"),
            ("admission", "Admission"),
            ("preliminary", "Preliminary"),
            ("referral", "Referral"),
            ("background", "Background"),
            ("concurrent", "Concurrent"),
            ("complications", "Complications"),
            ("related", "Related"),
        ],
        string="Type",
        readonly=True,
    )
    patient_visit_id = fields.Many2one(
        "his.patient_visit", string="Patient Visit", readonly=True
    )
    patient_id = fields.Many2one("his.patient", string="Patient", readonly=True)
    doctor_id = fields.Many2one("hr.employee", string="Doctor", readonly=True)
    create_date = fields.Datetime(string="Create Date", readonly=True)
    main_service_id = fields.Many2one(
        "product.product", string="Main Service", readonly=True
    )
    date = fields.Date(
        related="patient_visit_id.date", string="Visit Date", readonly=True
    )

    def init(self):
        # recreate the SQL view
        tools.drop_view_if_exists(self.env.cr, "his_selected_diagnosis_view")
        self.env.cr.execute("""
            CREATE VIEW his_selected_diagnosis_view AS (
                SELECT
                    sd.id as id,
                    sd.code as code,
                    sd.name as name,
                    sd.category_id as category_id,
                    sd.type as type,
                    sd.patient_visit_id as patient_visit_id,
                    pv.patient_id as patient_id,
                    pv.doctor_id as doctor_id,
                    sd.create_date as create_date,
                    pv.main_service_id as main_service_id
                FROM his_selected_diagnosis sd
                LEFT JOIN his_patient_visit pv ON pv.id = sd.patient_visit_id
            )
        """)
