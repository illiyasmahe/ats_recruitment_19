# -*- coding: utf-8 -*-
#############################################################################
import requests

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
from odoo import http
from werkzeug.urls import url_encode
from urllib.parse import quote
import base64
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.portal.controllers.portal import pager
import secrets

class AtsWebsiteJobs(http.Controller):

    @http.route('/linkedin/login', type='http', auth='public', website=True)
    def linkedin_login(self):
        config = request.env['res.config.settings'].sudo().get_values()
        client_id = config.get('linkedin_client_id')
        redirect_uri = config.get('linkedin_redirect_uri')

        state = secrets.token_urlsafe(16)
        request.session['linkedin_oauth_state'] = state

        url = (
            f"https://www.linkedin.com/oauth/v2/authorization?"
            f"response_type=code&client_id={client_id}"
            f"&redirect_uri={quote(redirect_uri, safe='')}"
            f"&state={state}"
            f"&scope=openid%20profile%20email%20w_member_social"
        )
        return url

    @http.route('/linkedin/callback', type='http', auth='public', website=True)
    def linkedin_callback(self, code=None, state=None, **kw):
        import requests

        if not code:
            return "<h3>Authorization failed: missing code</h3>"

        # # Verify state to prevent CSRF
        # if state != request.session.get('linkedin_oauth_state'):
        #     return "<h3>Invalid state</h3>"

        # Read LinkedIn app settings
        config = request.env['res.config.settings'].sudo().get_values()
        client_id = config.get('linkedin_client_id')
        client_secret = config.get('linkedin_client_secret')
        redirect_uri = config.get('linkedin_redirect_uri')

        # Exchange code for access token
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        token_resp = requests.post(token_url, data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret,
        }).json()

        access_token = token_resp.get('access_token')
        config_settings = request.env['res.config.settings'].sudo().create({})

        # Assign the field value
        config_settings.linkedin_access_token = access_token

        # Call set_values() without arguments
        config_settings.set_values()

        if not access_token:
            err_desc = token_resp.get('error_description') or token_resp.get('error')
            return f"<h3>Failed to get access token: {err_desc}</h3>"

        return request.render('ats_website_jobs.linkedin_verify_success_page')

    @http.route('/linkedin/signup', type='http', auth='public', website=True)
    def linkedin_signup(self):
        config = request.env['res.config.settings'].sudo().get_values()
        access_token = config.get('linkedin_access_token')

        if not access_token:
            return f"<h3>Failed to get access token</h3>"

        headers = {'Authorization': f'Bearer {access_token}'}

        # Fetch member info from userinfo endpoint
        userinfo = requests.get('https://api.linkedin.com/v2/userinfo', headers=headers).json()

        # Extract fields safely
        name = userinfo.get('name', '')
        first_name = userinfo.get('given_name', '')
        last_name = userinfo.get('family_name', '')
        email = userinfo.get('email', '')  # may be empty if not verified
        linkedin_id = userinfo.get('sub', '')
        picture = userinfo.get('picture', '')
        email_verified = userinfo.get('email_verified', '')

        # Send data back to parent popup
        return f"""
                    <script>
                        if(window.opener){{
                            window.opener.postMessage({{
                                linkedinProfile: {{
                                    name: "{name}",
                                    email: "{email}",
                                    email_verified: "{email_verified}",
                                    sub: "{linkedin_id}",
                                    picture: "{picture}",
                                }}
                            }}, window.location.origin);
                            window.close();
                        }} else {{
                            document.body.innerHTML = "<h3>Cannot communicate with parent window</h3>";
                        }}
                    </script>
                """

    @http.route(['/jobs', '/jobs/page/<int:page>'], type='http', auth='public', website=True)
    def job_list(self, page=1, search='', **kw):
        domain = [('position_state', '=', 'open')]

        if search:
            domain += ['|', ('name', 'ilike', search), ('project_id.name', 'ilike', search)]

        job_model = request.env['project.task'].sudo()

        total_jobs = job_model.search_count(domain)

        pager_data = pager(
            url="/jobs",
            total=total_jobs,
            page=page,
            step=9,
            url_args={'search': search}  # IMPORTANT
        )

        jobs = job_model.search(
            domain,
            limit=9,
            offset=pager_data['offset']
        )

        return request.render(
            "ats_website_jobs.job_list_page",
            {
                'jobs': jobs,
                'pager': pager_data,
                'search': search,
                'keep': QueryURL('/jobs', search=search)
            }
        )

    @http.route('/jobs/sidebar/<int:job_id>', type='http', auth='public', website=True)
    def job_sidebar(self, job_id):
        job = request.env['project.task'].sudo().browse(job_id)

        return request.render(
            'ats_website_jobs.job_detail_sidebar',
            {'job': job}
        )

    @http.route('/privacy-policy', type='http', auth='public', website=True)
    def privacy_policy(self):
        return request.render(
            'ats_website_jobs.privacy_policy',
        )

    # Job detail
    @http.route('/jobs/<int:job_id>', type='http', auth='public', website=True)
    def job_detail(self, job_id):

        job = request.env['project.task'].sudo().browse(job_id)

        return request.render(
            'ats_website_jobs.job_detail_page',
            {'job': job}
        )

    # Apply page
    @http.route('/jobs/apply/<int:job_id>', type='http', auth='public', website=True)
    def job_apply(self, job_id):

        job = request.env['project.task'].sudo().browse(job_id)

        # Fetch system parameter for LinkedIn signup
        signup_with_linkedin = request.env['ir.config_parameter'].sudo().get_param('ats_website_jobs.signup_with_linkedin') == 'True'

        return request.render(
            'ats_website_jobs.job_apply_page',
            {
                'job': job,
                'signup_with_linkedin': signup_with_linkedin,  # pass to template
            }
        )

    # Submit application

    @http.route('/jobs/apply/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def submit_application(self, **post):

        job_id = post.get('job_id')
        job = request.env['project.task'].sudo().browse(int(job_id))
        name = post.get('name')
        email = post.get('email')
        phone = post.get('phone')
        alt_phone = post.get('alt_phone')
        linkedin = post.get('linkedin')
        cover_letter = post.get('cover_letter')

        linkedin_sub = post.get('linkedin_sub')
        linkedin_picture = post.get('linkedin_picture')
        linkedin_verified = post.get('linkedin_email_verified')

        # 🚀 If LinkedIn registration → redirect confirm page
        if linkedin_sub:
            params = {
                'job_id': job_id,
                'name': name,
                'email': email,
                'picture': linkedin_picture,
                'sub': linkedin_sub,
                'email_verified': linkedin_verified,
            }

            return request.redirect('/jobs/apply/confirm?' + url_encode(params))

        Applicant = request.env['ats.applicant'].sudo()

        # CHECK DUPLICATE EMAIL
        if email and Applicant.search([('email', '=', email)], limit=1):
            return request.render(
                "ats_website_jobs.job_apply_page",
                {
                    'job': job,
                    'error': "This email is already used for an application."
                }
            )

        # CHECK DUPLICATE MOBILE
        if phone and Applicant.search([('mobile', '=', phone)], limit=1):
            return request.render(
                "ats_website_jobs.job_apply_page",
                {
                    'job': job,
                    'error': "This mobile number already applied."
                }
            )

        # CHECK DUPLICATE LINKEDIN
        if linkedin and Applicant.search([('linkedin', '=', linkedin)], limit=1):
            return request.render(
                "ats_website_jobs.job_apply_page",
                {
                    'job': job,
                    'error': "This LinkedIn profile already applied."
                }
            )

        # HANDLE RESUME
        resume_file = request.httprequest.files.get('resume')
        resume_data = False
        resume_filename = False

        if resume_file:
            resume_data = base64.b64encode(resume_file.read())
            resume_filename = resume_file.filename

        # CREATE APPLICANT
        Applicant.create({
            'name': name,
            'email': email,
            'mobile': phone,
            'mobile2': alt_phone,
            'linkedin_url': linkedin,
            'description': cover_letter,
            'task_id': int(job_id),
            'resume': resume_data,
            'resume_filename': resume_filename,
        })

        return request.render("ats_website_jobs.job_apply_success_page")

    @http.route('/jobs/apply/confirm', type='http', auth='public', website=True)
    def linkedin_confirm(self, **kw):

        return request.render(
            "ats_website_jobs.job_application_confirmation",
            {
                'job_id': kw.get('job_id'),
                'name': kw.get('name'),
                'email': kw.get('email'),
                'picture': kw.get('picture'),
                'sub': kw.get('sub'),
                'email_verified': kw.get('email_verified'),
            }
        )

    @http.route('/jobs/linkedin/confirm', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def linkedin_confirm_submit(self, **post):

        job_id = post.get('job_id')
        name = post.get('name')
        email = post.get('email')
        phone = post.get('phone')
        alt_phone = post.get('alt_phone')
        linkedin = post.get('linkedin')
        cover_letter = post.get('cover_letter')

        Applicant = request.env['ats.applicant'].sudo()

        # HANDLE RESUME
        resume_file = request.httprequest.files.get('resume')
        resume_data = False
        resume_filename = False

        if resume_file:
            resume_data = base64.b64encode(resume_file.read())
            resume_filename = resume_file.filename

        # CREATE APPLICANT
        Applicant.create({
            'name': name,
            'email': email,
            'mobile': phone,
            'mobile2': alt_phone,
            'linkedin_url': linkedin,
            'description': cover_letter,
            'task_id': int(job_id) if job_id else False,
            'resume': resume_data,
            'resume_filename': resume_filename,
        })

        # SHOW SUCCESS PAGE
        return request.render("ats_website_jobs.job_apply_success_page")

    # Thank you page
    @http.route('/jobs/thank-you', type='http', auth='public', website=True)
    def thank_you(self):
        return request.render('ats_website_jobs.job_thankyou')


    # General apply page
    @http.route('/apply', type='http', auth='public', website=True)
    def general_apply(self):
        return request.render('ats_website_jobs.apply_page')

    @http.route('/apply/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def general_apply_submit(self, **post):

        name = post.get('name')
        email = post.get('email')
        phone = post.get('phone')
        alt_phone = post.get('alt_phone')
        linkedin = post.get('linkedin')
        cover_letter = post.get('cover_letter')

        Applicant = request.env['ats.applicant'].sudo()

        # Duplicate validation
        if Applicant.search([('email', '=', email)], limit=1):
            return request.render('ats_website_jobs.apply_page', {
                'error': 'Email already applied.'
            })

        if Applicant.search([('mobile', '=', phone)], limit=1):
            return request.render('ats_website_jobs.apply_page', {
                'error': 'Mobile number already applied.'
            })

        if linkedin and Applicant.search([('linkedin', '=', linkedin)], limit=1):
            return request.render('ats_website_jobs.apply_page', {
                'error': 'LinkedIn already applied.'
            })

        # Resume
        resume_file = request.httprequest.files.get('resume')

        resume_data = False
        resume_filename = False

        if resume_file:
            resume_data = base64.b64encode(resume_file.read())
            resume_filename = resume_file.filename

        # Create or get the general candidate task
        Task = request.env['project.task'].sudo()
        general_task = Task.search([('name', '=', 'General Candidate')], limit=1)

        if not general_task:
            general_task = Task.create({
                'name': 'General Candidate',
                'project_id': request.env['project.project'].search([], limit=1).id,  # assign to a default project
                'stage_id': request.env['project.task.type'].search([('name', '=', 'Paused')], limit=1).id,
                'description': 'This task is for general candidate applications',
            })

        Applicant.create({
            'name': name,
            'email': email,
            'mobile': phone,
            'mobile2': alt_phone,
            'linkedin_url': linkedin,
            'description': cover_letter,
            'resume': resume_data,
            'resume_filename': resume_filename,
            'task_id': general_task.id if general_task else False,
            'is_general_candidate':True
        })

        return request.render("ats_website_jobs.job_apply_success_page")