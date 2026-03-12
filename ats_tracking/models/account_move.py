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
from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    task_id = fields.Many2one(
        'project.task',
        string="Job Position"
    )

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    applicant_id = fields.Many2one(
        'ats.applicant',
        string="Applicant"
    )

    job_position_id = fields.Many2one(
        'project.task',
        string="Job Position"
    )