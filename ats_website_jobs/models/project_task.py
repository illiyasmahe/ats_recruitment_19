import requests
from odoo import models, fields
from odoo.exceptions import UserError

class ProjectTask(models.Model):
    _inherit = "project.task"

    linkedin_post_id = fields.Char(string="LinkedIn Post ID", readonly=True)
    linkedin_oauth_state = fields.Char(string="LinkedIn OAuth State")
    linkedin_status = fields.Selection([
        ('not_published', 'Not Published'),
        ('published', 'Published')
    ], string="LinkedIn Status", default='not_published')

    linkedin_author_type = fields.Selection([
        ('person', 'Person'),
        ('company', 'Company')
    ], default='person', string="LinkedIn Author Type")

    linkedin_author_urn = fields.Char("LinkedIn Author URN", help="URN of person or company")
    linkedin_apply_link = fields.Char("Apply Link", help="URL for job application")
    linkedin_text = fields.Text("LinkedIn Post Text", help="Text content for LinkedIn post")
    linkedin_share_media_category = fields.Selection([
        ('NONE', 'None'),
        ('ARTICLE', 'Article'),
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video')
    ], default='NONE', string="Media Category")
    linkedin_visibility = fields.Selection([
        ('PUBLIC', 'Public'),
        ('CONNECTIONS', 'Connections'),
    ], default='PUBLIC', string="Post Visibility")

    def action_post_linkedin(self):
        import requests
        from odoo.exceptions import UserError
        from odoo.tools import html2plaintext

        config = self.env['res.config.settings'].sudo().get_values()
        token = config.get('linkedin_access_token')
        if not token:
            raise UserError("Access Token Not Found. Please verify LinkedIn account.")

        # Determine author URN
        if self.linkedin_author_urn:
            author_urn = self.linkedin_author_urn
        else:
            # Fallback: fetch current user ID
            profile_res = requests.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if profile_res.status_code != 200:
                raise UserError(profile_res.text)
            profile = profile_res.json()
            person_id = profile.get("sub")
            author_urn = f"urn:li:person:{person_id}"

        # Build dynamic text
        description_text = html2plaintext(self.description or "")
        post_text = (self.linkedin_text or f"We're Hiring: {self.name}\n\n{description_text}")
        if self.linkedin_apply_link:
            post_text += f"\n\nApply here: {self.linkedin_apply_link}"

        # Build payload
        data = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": post_text},
                    "shareMediaCategory": self.linkedin_share_media_category or "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": self.linkedin_visibility or "PUBLIC"
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            json=data,
            headers=headers
        )

        if response.status_code in [200, 201]:
            # Save post ID and update status
            post_id = response.headers.get("x-restli-id") or response.json().get("id")
            self.linkedin_post_id = post_id
            self.linkedin_status = 'published'
            print("LinkedIn post created:", post_id)
        else:
            raise UserError(f"LinkedIn Post Failed: {response.status_code} - {response.text}")

    def action_unpublish_linkedin(self):
        import requests
        from odoo.exceptions import UserError

        config = self.env['res.config.settings'].sudo().get_values()
        token = config.get('linkedin_access_token')
        if not token:
            raise UserError("Access Token not found.")

        if not getattr(self, "linkedin_post_id", False):
            raise UserError("No LinkedIn post ID found to unpublish.")

        post_id = self.linkedin_post_id

        # Determine post type and extract numeric ID
        if post_id.startswith("urn:li:ugcPost:"):
            post_type = "ugcPosts"
            post_id = post_id.split(":")[-1]
        elif post_id.startswith("urn:li:share:"):
            post_type = "shares"
            post_id = post_id.split(":")[-1]
        else:
            raise UserError("Unknown LinkedIn post ID format.")

        delete_url = f"https://api.linkedin.com/v2/{post_type}/{post_id}"

        response = requests.delete(
            delete_url,
            headers={
                "Authorization": f"Bearer {token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
        )

        if response.status_code in [200, 204]:
            self.linkedin_post_id = False
            self.linkedin_status = 'not_published'
            print("LinkedIn post successfully deleted")
        else:
            raise UserError(f"Failed to delete LinkedIn post: {response.status_code} - {response.text}")