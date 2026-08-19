from odoo import api, models

# Job states considered terminal: the job will not change on its own anymore.
TERMINAL_JOB_STATES = ("done", "failed", "cancelled")


class QueueJobBatch(models.Model):
    _inherit = "queue.job.batch"

    @api.model
    def get_new_batch(self, name, **kwargs):
        vals = kwargs.copy()
        # Use current company from context instead of user's default company
        company_id = self.env.company.id

        if "company_id" in self.env.context:
            company_id = self.env.context["company_id"]

        vals.update(
            {
                "user_id": self.env.uid,
                "name": name,
                "state": "draft",
                "company_id": company_id,
            }
        )
        return self.sudo().create(vals).with_user(self.env.uid)

    def check_state(self):
        """Finish the batch once every job reached a terminal state.

        The base ``queue_job_batch`` module only marks the batch as
        ``finished`` when *all* jobs are ``done``. If a single job ends in
        ``failed`` (or ``cancelled``), the batch stays in ``progress``
        forever, and so does any record whose state is related to it
        (e.g. ``his.share_and_bonus_recalc_job``).

        Here a batch is finished as soon as no job is still pending,
        regardless of whether it succeeded or failed.
        """
        self.ensure_one()
        if self.state == "enqueued" and any(
            job.state not in ["pending", "enqueued"] for job in self.job_ids
        ):
            self.write({"state": "progress"})
        if self.state != "progress":
            return True
        if self.job_ids and all(
            job.state in TERMINAL_JOB_STATES for job in self.job_ids
        ):
            self.write({"state": "finished", "is_read": False})
        return True


class QueueJob(models.Model):
    _inherit = "queue.job"

    def write(self, vals):
        """Re-check the batch state also on ``failed``/``cancelled`` jobs.

        The base ``queue_job_batch`` module re-evaluates the batch only
        when a job becomes ``done``. A job that ends in ``failed`` or
        ``cancelled`` never triggers the check, so the batch never
        finishes. We add that missing trigger here.
        """
        new_state = vals.get("state")
        if new_state in ("failed", "cancelled"):
            batches = self.env["queue.job.batch"]
            for record in self:
                if record.job_batch_id and record.state != new_state:
                    batches |= record.job_batch_id
            for batch in batches:
                # Delayed to avoid two jobs writing the same batch at once.
                batch.with_delay().check_state()
        return super().write(vals)
