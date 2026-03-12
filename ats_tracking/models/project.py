from odoo import models, fields

class Project(models.Model):
    _inherit = "project.project"

    applicant_stage_ids = fields.Many2many(
        'ats.applicant.stage',
        'project_applicant_stage_rel',
        'project_id',
        'stage_id',
        string="Applicant Stages"
    )

    description = fields.Text(
        string="Description"
    )