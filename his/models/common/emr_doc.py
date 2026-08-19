import ast
import json
from datetime import timedelta

from odoo import models, fields, api, _, modules, exceptions
from odoo.fields import Datetime
import base64
from ...utils.selections import categ_selection


class EmrDocument(models.Model):
    _name = "his.emr_doc"
    _inherit = "mail.thread"
    _description = "EMR Document Records"

    name = fields.Char(string="Name", readonly=True, translate=True)
    date = fields.Date(string="Date", default=fields.Date.context_today)
    report_id = fields.Many2one("report.report", string="Report")
    author_id = fields.Many2one(
        "res.users", string="Author", default=lambda self: self.env.user
    )
    data = fields.Text(string="Data")
    patient_visit_id = fields.Many2one(
        "his.patient_visit", string="Patient Visit", ondelete="cascade"
    )
    pdf_file = fields.Binary(string="PDF File")
    patient_id = fields.Many2one(
        "his.patient", string="Patient", related="patient_visit_id.patient_id"
    )
    report_model = fields.Char("Report Model", index=True)
    report_object_id = fields.Integer("Report Object ID", index=True)
    is_save_history = fields.Boolean("Save History")
    active = fields.Boolean("Active", default=True)
    type = fields.Selection(categ_selection, "EMR Document Type")
    order_detail_id = fields.Many2one(
        "his.order_detail", string="Order detail", ondelete="restrict"
    )
    product_type_id = fields.Many2one(
        "his.category_base", string="Product Type", related="order_detail_id.product_type", store=True
    )
    attachment_url = fields.Char(
        string="Attachment URL",
        compute="_compute_attachment_url",
        help="Secure URL with access token for downloading the PDF file"
    )


    def unlink(self):
        user = self.env.user
        if not self.env.context.get("_force_unlink", False):
            for rec in self:
                if rec.author_id.id != user.id and not user.has_group("his.group_his_manager"):
                    raise exceptions.AccessError(_("You are not allowed to delete this EMR document."))

                is_done = rec.patient_visit_id and rec.patient_visit_id.is_done

                if is_done:
                    emr_doc_count = self.search_count([
                        ("report_id", "=", rec.report_id.id),
                        ("report_model", "=", rec.report_model),
                        ("report_object_id", "=", rec.report_object_id),
                        ("active", "=", True),
                    ])
                    if emr_doc_count <= 1:
                        raise exceptions.UserError(_("You cannot delete the last EMR document for a completed service."))

        self.write({
            "active": False,
        })

    def _get_attachment(self):
        self.ensure_one()
        return self.env["ir.attachment"].sudo().search(
            [("res_id", "=", self.id), ("res_model", "=", "his.emr_doc"), ("res_field", "=", "pdf_file")], limit=1, order="id desc"
        )

    def _filter_latest_versions(self):
        """Keep only the latest version of each conclusion (zaklyucheniye).

        Saving a conclusion with is_save_history creates a new his.emr_doc row
        per save, so a single conclusion accumulates several versions. The
        registry (registratura) must surface only the most recent one.

        One order_detail (or visit) can legitimately hold SEVERAL distinct
        conclusions filled from DIFFERENT templates -- in the ambulatory flow a
        doctor may fill more than one document per service. Those are separate
        documents, not re-saves of one, so versions are grouped by
        (subject, report template) and the latest of EACH template survives.
        Grouping by subject alone would collapse every template into one and
        drop real documents.

        Subject -- the thing the conclusion is about -- precedence:

          1. order_detail (the service) -- most specific;
          2. (report_model, report_object_id) -- for docs without an
             order_detail (e.g. ris.order/fis.order external PDFs);
          3. patient_visit -- last resort.

        order_detail must win over report_object_id: doctor docs all store
        report_object_id = patient_visit, so keying on that first would merge
        every service of a visit into a single group. Latest = highest id.
        Records with no subject at all are kept as-is.
        """
        latest = {}
        keep_ids = set()
        for rec in self:
            if rec.order_detail_id:
                subject = ("his.order_detail", rec.order_detail_id.id)
            elif rec.report_model and rec.report_object_id:
                subject = (rec.report_model, rec.report_object_id)
            elif rec.patient_visit_id:
                subject = ("his.patient_visit", rec.patient_visit_id.id)
            else:
                keep_ids.add(rec.id)
                continue
            key = (subject, rec.report_id.id)
            if rec.id > latest.get(key, 0):
                latest[key] = rec.id
        keep_ids.update(latest.values())
        return self.browse(keep_ids)


    @api.depends("pdf_file")
    def _compute_attachment_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for record in self:
            attachment_id = record._get_attachment()
            if attachment_id:
                # Generate access token ifgenerate_access_token not exists
                attachment_id.sudo().generate_access_token()
                # Build URL with token for secure access
                record.attachment_url = (
                    f"{base_url}/web/content/{attachment_id.id}"
                    f"?access_token={attachment_id.access_token}&download=true"
                )
            else:
                record.attachment_url = False

    @api.model
    def preview_emr_report(
        self, report_id, html_pages=None, header=None, footer=None, object_id=None
    ):
        report = self.env["report.report"].browse(report_id)
        pdf_content = report.generate_pdf(
            html_pages, header, footer, object_id=object_id
        )
        encoded_pdf = base64.encodebytes(pdf_content)
        pdf_preview = self.env["his.pdf_viewer"].create({"pdf_file": encoded_pdf})
        return {
            "name": report.name,
            "type": "ir.actions.act_window",
            "res_model": "his.pdf_viewer",
            "res_id": pdf_preview.id,
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "new",
            "context": {
                "bin_size": False,
                "create": False,
                "edit": False,
            },
        }


    def _parse_data_safe(self):
        """Parse self.data as JSON. Return {} for missing/invalid input.

        his.emr_doc.data is fields.Text and is left NULL by external-system
        sources (ris/fis/lis/checkup_summary PDF-only docs). All readers
        must go through this helper instead of json.loads directly.
        """
        self.ensure_one()
        text = self.data
        if not text or not isinstance(text, str):
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback for legacy/external-system payloads stored as Python
            # repr (single-quoted dicts). literal_eval handles embedded
            # apostrophes inside double-quoted values correctly, where a
            # naive str.replace("'", '"') would corrupt them.
            try:
                return ast.literal_eval(text)
            except (ValueError, SyntaxError):
                return {}

    def get_template_and_data(self):
        """Return rendered HTML pages, saved inputs data, and report parameters for the emr_doc_template widget."""
        self.ensure_one()
        report_data = {}
        if self.report_id and self.report_model and self.report_object_id:
            report_data = self.report_id.get_report_data(
                self.report_model,
                self.report_object_id,
            )

        html_pages = self.report_id._get_template_page_payloads(
            model_name=self.report_model,
            object_id=self.report_object_id,
        )
        for page in html_pages:
            page["report"] = page.pop("report_definition", "{}") or "{}"

        return {
            "html_pages": json.dumps(html_pages),
            "data": self.data or "{}",
            "report_data": json.dumps(report_data),
            "report_id": self.report_id.id,
        }

    def action_show_pdf_report(self):
        self.ensure_one()
        if not self.pdf_file:
            raise exceptions.UserError(
                _("No PDF file available for this EMR document.")
            )
        encoded_content = self.pdf_file

        pdf_preview = (
            self.env["his.pdf_viewer"]
            .with_context()
            .create(
                {   "pdf_file": encoded_content,
                    "report_model": self.report_model,
                    "report_object_id": self.report_object_id,
                }
            )
        )

        return {
            "name": "Result - %s" % (self.patient_id.name),
            "type": "ir.actions.act_window",
            "res_model": "his.pdf_viewer",
            "res_id": pdf_preview.id,
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "new",
            "context": {
                "bin_size": False,
                "create": False,
                "edit": False,
            },
        }


class EmrDocumentDraft(models.Model):
    _name = "his.emr_doc_draft"
    _description = "EMR Document Draft Records"
    _order = "id desc"

    report_id = fields.Many2one("report.report", string="Report", required=True)
    author_id = fields.Many2one(
        "res.users", string="Author", default=lambda self: self.env.user
    )
    date = fields.Date(string="Date", default=fields.Date.context_today)
    patient_visit_id = fields.Many2one("his.patient_visit", string="Patient Visit")
    report_data = fields.Json(string="Data")
    is_autosave = fields.Boolean(
        string="Autosave",
        default=False,
        index=True,
        help="True for drafts produced by navigation autosave; False for explicit user saves.",
    )

    @api.model
    def write_last_visit(self, data):
        report_data = data.get("emr_draft_data")
        if report_data is None:
            return

        # Public RPC door: both ids come straight from the browser. Confirm the
        # caller may actually read the visit and the report before filing a
        # draft against them, or any user with the model ACL can create rows
        # pointing at encounters they have no business with. author_id is never
        # taken from the payload, so a draft can only ever be filed as oneself.
        visit = self.env["his.patient_visit"].browse(
            data.get("patient_visit_id")
        ).exists()
        report = self.env["report.report"].browse(data.get("report_id")).exists()
        if not visit or not report:
            return
        for record in (visit, report):
            record.check_access_rights("read")
            record.check_access_rule("read")

        existing_doc = self.search([
            ("report_id", "=", data.get("report_id")),
            ("patient_visit_id", "=", data.get("patient_visit_id")),
            ("author_id", "=", self.env.user.id),
            ("is_autosave", "=", True),
        ], order="id desc", limit=1)

        if existing_doc:
            existing_doc.write({
                "report_data": report_data,
            })
        else:
            self.create({
                "report_data": report_data,
                "patient_visit_id": data.get("patient_visit_id"),
                "report_id": data.get("report_id"),
                "author_id": self.env.user.id,
                "is_autosave": True,
            })

    @api.model
    def _cron_cleanup_autosave(self):
        """Daily cleanup for navigation autosave rows.

        Explicit drafts (is_autosave=False) are never touched. An autosave row
        is removed when any of the following holds:
          * its visit is closed (patient_visit_id.is_done) — the encounter
            won't be reopened, so the snapshot is dead weight;
          * its visit is missing (orphan) — the parent visit was deleted;
          * it is older than 7 days — safety net for visits that closed via
            non-ORM paths or events that never fired.
        """
        cutoff = Datetime.now() - timedelta(days=7)

        self.sudo().search([
            ("is_autosave", "=", True),
            "|", "|",
            ("patient_visit_id", "=", False),
            ("patient_visit_id.is_done", "=", True),
            ("create_date", "<", cutoff),
        ]).unlink()
