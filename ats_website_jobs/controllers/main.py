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
from odoo import http
from urllib.parse import quote
import base64
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.portal.controllers.portal import pager

class AtsWebsiteJobs(http.Controller):
    REDIRECT_URI = '/linkedin/callback'


    @http.route('/linkedin/login', type='http', auth='public', website=True)
    def linkedin_login(self):
        # Read values from settings
        config = request.env['res.config.settings'].sudo().get_values()
        client_id = config.get('linkedin_client_id')
        redirect_uri = config.get('linkedin_redirect_uri')

        if not client_id or not redirect_uri:
            return "LinkedIn OAuth is not configured in settings."

        # Make sure redirect_uri is URL-encoded
        redirect_uri_encoded = quote(redirect_uri, safe='')

        # Build LinkedIn auth URL
        url = (
            f"https://www.linkedin.com/oauth/v2/authorization?"
            f"response_type=code&client_id={client_id}"
            f"&redirect_uri={redirect_uri_encoded}"
            f"&scope=r_liteprofile%20r_emailaddress"
        )

        return request.redirect(url)

    @http.route('/linkedin/callback', type='http', auth='public', website=True)
    def linkedin_callback(self, code=None, **kw):
        if not code:
            return "Authorization failed"

        # Read values from settings
        config = request.env['res.config.settings'].sudo().get_values()
        client_id = config.get('linkedin_client_id')
        client_secret = config.get('linkedin_client_secret')
        redirect_uri = config.get('linkedin_redirect_uri')

        # Exchange code for access token
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret,
        }
        import requests
        response = requests.post(token_url, data=data).json()
        access_token = response.get('access_token')

        if not access_token:
            return "Failed to get access token"

        headers = {'Authorization': f'Bearer {access_token}'}
        profile = requests.get('https://api.linkedin.com/v2/me', headers=headers).json()
        email = requests.get(
            'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))',
            headers=headers
        ).json()

        return request.render('ats_website_jobs.apply_page', {
            'name': profile.get('localizedFirstName', '') + ' ' + profile.get('localizedLastName', ''),
            'email': email['elements'][0]['handle~']['emailAddress'],
            'linkedin': profile.get('id'),
        })

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

        return request.render(
            'ats_website_jobs.job_apply_page',
            {'job': job}
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
            'linkedin': linkedin,
            'description': cover_letter,
            'task_id': int(job_id),
            'resume': resume_data,
            'resume_filename': resume_filename,
        })

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