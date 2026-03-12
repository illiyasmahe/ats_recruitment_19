# -*- coding: utf-8 -*-
#############################################################################

#    Alhodood Technologies.
#
#    Copyright (C) 2026-TODAY Alhodood Technologies(<https://www.alhodood.com>)
#    Author: Alhodood Technologies(<https://www.alhodood.com>)
#
#    You can modify it under the terms of the GNU Affero General Public License
#    (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License (AGPL v3) for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, api

class AtsApplicant(models.Model):
    _name = "ats.applicant"
    _description = "Job Applicant"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Applicant Name",
        required=True,
        tracking=True
    )

    task_id = fields.Many2one(
        'project.task',
        string="Applied Job",
        required=True
    )

    stage_id = fields.Many2one(
        'ats.applicant.stage',
        string="Stage",
        tracking=True,
        default=lambda self: self.env['ats.applicant.stage'].search([], limit=1)
    )

    recruiter_id = fields.Many2one(
        'res.users',
        string="Recruiter"
    )

    evaluation = fields.Text(
        string="Evaluation"
    )

    mobile = fields.Char(
        string="Mobile",
        required=True
    )

    mobile2 = fields.Char(
        string="Mobile 2"
    )

    linkedin_url = fields.Char(
        string="LinkedIn URL"
    )

    email = fields.Char(
        string="Email"
    )

    tag_ids = fields.Many2many(
        'project.tags',
        string="Tags"
    )

    create_date = fields.Datetime(
        string="Creation Date",
        readonly=True
    )

    resume = fields.Binary(
        string="Resume"
    )

    resume_filename = fields.Char()

    meeting_id = fields.Many2one(
        'calendar.event',
        string="Interview Meeting"
    )

    interview_status = fields.Selection([
        ('pending', 'Pending'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected')
    ], string="Interview Status", compute="_compute_interview_status", store=True)

    is_stage_readonly = fields.Boolean(
        string="Readonly by Stage",
        compute="_compute_is_stage_readonly",
        store=True  # store=True allows using it in XML attrs
    )

    @api.depends('stage_id')
    def _compute_is_stage_readonly(self):
        for rec in self:
            # Example: make readonly if stage has a custom boolean `is_readonly` or any logic
            if rec.stage_id:
                rec.is_stage_readonly = getattr(rec.stage_id, 'is_readonly', False)
            else:
                rec.is_stage_readonly = False

    @api.depends('stage_id')
    def _compute_interview_status(self):
        for rec in self:
            if rec.stage_id.is_hired:
                rec.interview_status = 'hired'
            elif rec.stage_id.is_rejected:
                rec.interview_status = 'rejected'
            else:
                rec.interview_status = 'pending'

    # -------------------------
    # UNIQUE VALIDATION
    # -------------------------

    _sql_constraints = [

        ('mobile_unique',
         'unique(mobile)',
         'Mobile number must be unique'),

        ('mobile2_unique',
         'unique(mobile2)',
         'Secondary mobile must be unique'),

        ('email_unique',
         'unique(email)',
         'Email must be unique'),

        ('linkedin_unique',
         'unique(linkedin_url)',
         'LinkedIn must be unique')
    ]

    def action_schedule_interview(self):
        meeting = self.env['calendar.event'].create({
            'name': 'Interview - %s' % self.name,
            'partner_ids': [(6, 0, [self.recruiter_id.partner_id.id])],
            'description': 'Interview for %s' % self.task_id.name,
        })

        self.meeting_id = meeting.id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'calendar.event',
            'view_mode': 'form',
            'res_id': meeting.id,
        }

    @api.onchange('task_id')
    def _onchange_task(self):
        if self.task_id and self.task_id.project_id:
            return {
                'domain': {
                    'stage_id': [
                        ('project_id', '=', self.task_id.project_id.id)
                    ]
                }
            }