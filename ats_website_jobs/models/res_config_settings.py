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

class LinkedinSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    linkedin_client_id = fields.Char(string="LinkedIn Client ID")
    linkedin_client_secret = fields.Char(string="LinkedIn Client Secret")
    linkedin_redirect_uri = fields.Char(string="LinkedIn Redirect URI")
    linkedin_access_token = fields.Char(string="LinkedIn Access Token")

    signup_with_linkedin = fields.Boolean(string="Sign up with LinkedIn")

    def get_values(self):
        res = super().get_values()
        IrConfig = self.env['ir.config_parameter'].sudo()
        res.update(
            linkedin_client_id=IrConfig.get_param('ats_website_jobs.linkedin_client_id'),
            linkedin_client_secret=IrConfig.get_param('ats_website_jobs.linkedin_client_secret'),
            linkedin_redirect_uri=IrConfig.get_param('ats_website_jobs.linkedin_redirect_uri'),
            linkedin_access_token=IrConfig.get_param('ats_website_jobs.linkedin_access_token'),
            signup_with_linkedin=IrConfig.get_param('ats_website_jobs.signup_with_linkedin'),
        )
        return res

    def set_values(self):
        super().set_values()
        IrConfig = self.env['ir.config_parameter'].sudo()
        IrConfig.set_param('ats_website_jobs.linkedin_client_id', self.linkedin_client_id or '')
        IrConfig.set_param('ats_website_jobs.linkedin_client_secret', self.linkedin_client_secret or '')
        IrConfig.set_param('ats_website_jobs.linkedin_redirect_uri', self.linkedin_redirect_uri or '')
        IrConfig.set_param('ats_website_jobs.linkedin_access_token', self.linkedin_access_token or '')
        IrConfig.set_param('ats_website_jobs.signup_with_linkedin', self.signup_with_linkedin or '')