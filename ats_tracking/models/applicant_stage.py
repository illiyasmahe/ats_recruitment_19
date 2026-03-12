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