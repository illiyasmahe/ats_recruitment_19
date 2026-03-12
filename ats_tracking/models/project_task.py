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
from datetime import date

class ProjectTask(models.Model):
    _inherit = "project.task"

    recruitment_manager_id = fields.Many2one(
        'res.users',
        string="Recruitment Manager"
    )

    team_member_ids = fields.Many2many(
        'res.users',
        string="Team Members"
    )

    contact_id = fields.Many2one(
        'res.partner',
        string="Point of Contact"
    )

    opened_positions = fields.Integer(
        string="Opened Positions"
    )
    closed_positions = fields.Integer(
        string="Closed Positions",
        compute="_compute_closed_positions"
    )
    remaining_positions = fields.Integer(
        string="Remaining Positions",
        compute="_compute_remaining_positions"
    )

    days_open = fields.Integer(
        string="Days Open",
        compute="_compute_days_open"
    )

    applicant_stage_ids = fields.Many2many(
        'ats.applicant.stage',
        string="Applicant Stages"
    )

    is_active_stage = fields.Boolean(
        compute="_compute_is_active_stage"
    )

    applicant_count = fields.Integer(
        string="Applications",
        compute="_compute_applicant_count"
    )

    position_state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ], default='draft', tracking=True)

    delayed_days = fields.Integer(
        string="Delayed Days",
        compute="_compute_delayed_days",
        store=True,
        help="Number of days the task is past its deadline"
    )

    @api.depends('project_id')
    def _compute_closed_positions(self):
        """Count of applicants in 'Hired' stage"""
        hired_stage = self.env['ats.applicant.stage'].search([('name', '=', 'Hired')], limit=1)
        for rec in self:
            if hired_stage:
                rec.closed_positions = self.env['ats.applicant'].search_count([
                    ('task_id', '=', rec.id),
                    ('stage_id', '=', hired_stage.id)
                ])
            else:
                rec.closed_positions = 0

    @api.depends('opened_positions', 'closed_positions')
    def _compute_remaining_positions(self):
        for rec in self:
            rec.remaining_positions = rec.opened_positions - rec.closed_positions

    @api.depends('date_deadline', 'create_date', 'position_state', 'write_date')
    def _compute_delayed_days(self):
        """Compute how many days the task is delayed past its deadline"""
        for rec in self:
            if rec.date_deadline:
                # convert datetime to date
                deadline_date = rec.date_deadline.date() if isinstance(rec.date_deadline,
                                                                       fields.Datetime) else rec.date_deadline

                # If task is closed, use write_date; else use today
                if rec.position_state == 'closed' and rec.write_date:
                    end_date = rec.write_date.date()
                else:
                    end_date = date.today()

                delta = (end_date - deadline_date.date()).days
                rec.delayed_days = delta if delta > 0 else 0
            else:
                rec.delayed_days = 0

    def action_pause(self):
        for rec in self:
            rec.position_state = 'paused'

    def action_close(self):
        for rec in self:
            rec.position_state = 'closed'

    def action_open(self):
        for rec in self:
            rec.position_state = 'open'

    def _compute_applicant_count(self):
        for rec in self:
            rec.applicant_count = self.env['ats.applicant'].search_count([
                ('task_id', '=', rec.id)
            ])

    def action_view_applicants(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'Applications',
            'res_model': 'ats.applicant',
            'view_mode': 'list,form,kanban',
            'domain': [('task_id', '=', self.id)],
            'context': {
                'default_task_id': self.id
            }
        }

    @api.depends('create_date', 'stage_id')
    def _compute_days_open(self):
        for rec in self:
            if rec.create_date:
                rec.days_open = (date.today() - rec.create_date.date()).days
            else:
                rec.days_open = 0

    def _compute_is_active_stage(self):
        for rec in self:
            if rec.position_state=='open':
                rec.is_active_stage = True
            else:
                rec.is_active_stage = False

    @api.depends('recruitment_manager_id', 'team_member_ids')
    def _sync_assignees(self):
        """Automatically add manager + team members to Assignees"""
        for rec in self:
            users = rec.team_member_ids.ids
            if rec.recruitment_manager_id:
                users.append(rec.recruitment_manager_id.id)
            rec.user_ids = [(6, 0, users)]

    # Button to add team member
    def action_add_team_member(self):
        return {
            'name': 'Manage Team Members',
            'type': 'ir.actions.act_window',
            'res_model': 'task.team.member.wizard',  # this is correct
            'domain': [],
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
                'default_user_ids': [(6, 0, self.team_member_ids.ids)],
            },
        }

    # Button to change manager
    def action_change_manager(self):
        return {
            'name': 'Manage Manager',
            'type': 'ir.actions.act_window',
            'res_model': 'task.manager.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
                'default_manager_id': self.recruitment_manager_id.id,
            },
        }

    @api.onchange('project_id')
    def _onchange_project(self):
        return {
            'domain': {
                'applicant_stage_id': [('project_id', '=', self.project_id.id)]
            }
        }