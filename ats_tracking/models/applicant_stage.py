from odoo import models, fields

class ApplicantStage(models.Model):
    _name = "ats.applicant.stage"
    _description = "Applicant Stage"
    _order = "sequence"

    name = fields.Char(string="Stage Name", required=True)

    project_id = fields.Many2one(
        'project.project',
        string="Project"
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10
    )

    description = fields.Text(
        string="Description"
    )

    active = fields.Boolean(
        string="Active",
        default=True
    )

    is_hired = fields.Boolean(
        string="Hired Stage"
    )

    is_rejected = fields.Boolean(
        string="Rejected Stage"
    )

    is_readonly = fields.Boolean(
        string="Is Readonly"
    )