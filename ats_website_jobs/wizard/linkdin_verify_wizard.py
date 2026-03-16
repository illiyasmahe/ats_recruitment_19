from odoo import models, fields
import requests

class LinkedinVerifyWizard(models.TransientModel):
    _name = "linkedin.verify.wizard"
    _description = "Verify LinkedIn Account"

    show_message = fields.Text(string="Click the button below to verify your LinkedIn account.")

    def action_open_linkedin(self):
        """Open LinkedIn login in a new tab"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = f"{base_url}/linkedin/login"
        response = requests.get(url)
        return {
            'type': 'ir.actions.act_url',
            'url': response.text,
            'target': 'new',  # opens in new tab
        }