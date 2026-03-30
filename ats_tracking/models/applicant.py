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
from html import unescape
import tempfile
import os
from ..pdf_data_extraction import parse_resume
import base64
import re

SKILL_WEIGHT = 0.4
EXPERIENCE_WEIGHT = 0.3
EDUCATION_WEIGHT = 0.2
KEYWORD_WEIGHT = 0.1

SKILL_MAP = {
    # programming
    "py": "python",
    "python3": "python",

    "js": "javascript",
    "nodejs": "node.js",

    # frameworks
    "django rest": "django",
    "drf": "django",

    # data / ai
    "ml": "machine learning",
    "ai": "artificial intelligence",

    # web
    "html5": "html",
    "css3": "css",

    # api
    "rest api": "api",
    "restful api": "api",
}

class SkillMaster(models.Model):
    _name = 'skill.master'
    _description = 'Skill Master'

    name = fields.Char(required=True)

class AtsApplicant(models.Model):
    _name = "ats.applicant"
    _order = "score desc, experience_years desc, id desc"
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

    is_general_candidate = fields.Boolean(string="General Candidate")

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

    description = fields.Text(
        string="Cover Letter"
    )

    pdf_text = fields.Text(
        string="PDF Text"
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

    github_url = fields.Char(
        string="GitHub",
        required=False
    )

    email = fields.Char(
        string="Email"
    )

    tag_ids = fields.Many2many(
        'project.tags',
        string="Tags"
    )

    skill_ids = fields.Many2many(
        'skill.master',
        'applicant_skill_rel',
        'applicant_id',
        'skill_id',
        string="Skills"
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

    invoice_line_id = fields.Many2one(
        'account.move.line',
        string="Invoice Line"
    )

    invoice_status = fields.Selection(
        [('not_invoiced', 'Not Invoiced'),
         ('invoiced', 'Invoiced')],
        string="Invoice Status",
        compute="_compute_invoice_status",
        store=True
    )
    stage_status_str = fields.Char(
        string="Stage Status",
        compute='_compute_stage_status_str',
        store=False
    )
    education = fields.Text("Education")  # store all education
    highest_education = fields.Char("Highest Education")

    experience_years = fields.Float("Experience (Years)")

    score = fields.Float("Match Score", compute="_compute_score", store=True)
    score_display = fields.Char(
        "Score %",
        compute="_compute_score_display",
        store=True
    )

    global_search_text = fields.Char(
        string="Global / Description",
        compute="_compute_global_search_text",
        store=True
    )

    rank = fields.Integer(
        string="Rank",
        compute="_compute_rank",
        store=True,
        index=True
    )

    task_stage_is_hired = fields.Boolean(
        related='stage_id.is_hired',
        string='Stage is Hired',
        store=True
    )

    task_stage_is_rejected = fields.Boolean(
        related='stage_id.is_rejected',
        string='Stage is Rejected',
        store=True
    )

    mail_status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected')
        ]
    )
    location_url = fields.Char(string="Location URL")

    accept_url = fields.Char(compute='_compute_urls')
    reject_url = fields.Char(compute='_compute_urls')

    def _compute_urls(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            record.accept_url = f"{base_url}/applicant/accept/{record.id}"
            record.reject_url = f"{base_url}/applicant/reject/{record.id}"

    def send_offer_email(self):
        self.ensure_one()

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        accept_url = f"{base_url}/applicant/accept/{self.id}"
        reject_url = f"{base_url}/applicant/reject/{self.id}"
        location_url = self.location_url or ''

        # Prepare HTML body
        body_html = f"""
        <p>Dear {self.name},</p>
        <p>Please confirm your attendance:</p>
        <p>
            <a href="{accept_url}" style="padding:10px 20px; background-color:#4CAF50; color:white; text-decoration:none; border-radius:5px;">Accept</a>
            &nbsp;
            <a href="{reject_url}" style="padding:10px 20px; background-color:#f44336; color:white; text-decoration:none; border-radius:5px;">Reject</a>
        </p>
        <p>Location: 
            <a href="{location_url}" style="color:#1a73e8;">View on Map</a>
        </p>
        <p>Regards,<br/>{self.task_id.partner_id.name}</p>
        """

        # Return Mail Composer
        return {
            'name': 'Mail To Applicant',
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model': 'ats.applicant',
                'default_res_ids': [self.id],
                'default_use_template': False,
                'default_body': body_html,
                'default_subject': 'Invitation',
            },
        }

    @api.depends('score', 'task_id')
    def _compute_rank(self):
        tasks = self.mapped('task_id')

        for task in tasks:
            applicants = self.sudo().search(
                [('task_id', '=', task.id)],
                order='score desc'
            )

            for i, rec in enumerate(applicants, start=1):
                rec.rank = i

    @api.depends('description', 'education', 'highest_education', 'experience_years', 'pdf_text')
    def _compute_global_search_text(self):
        for rec in self:
            text = " ".join([
                rec.description or "",
                rec.education or "",
                rec.highest_education or "",
                str(rec.experience_years) or "",
                rec.pdf_text or ""
            ])
            rec.global_search_text = text

    @api.depends('score')
    def _compute_score_display(self):
        for rec in self:
            rec.score_display = f"{int(rec.score)}%"

    @api.depends(
        'task_id',
        'skill_ids',
        'task_id.required_skill_ids',
        'experience_years',
        'education',
        'highest_education',
    )
    def _compute_score(self):
        """
            Compute a normalized matching score (0-100) for each applicant
            based on Skill Match, Experience Match, Education Match, and Keyword Match.
            """

        for rec in self:
            score = 0
            task = rec.task_id

            if not task:
                rec.score = 0
                continue

            # ---------------------------------
            # 1️⃣ SKILL MATCH (Most important)
            # ---------------------------------
            required_skills = task.required_skill_ids.mapped('name')
            applicant_skills = rec.skill_ids.mapped('name')

            match_count = 0
            for skill in required_skills:
                if any(skill.lower() == a.lower() for a in applicant_skills):
                    match_count += 1

            if required_skills:
                skill_score = (match_count / len(required_skills)) * 100
                score += skill_score * SKILL_WEIGHT

            # ---------------------------------
            # 2️⃣ EXPERIENCE MATCH
            # ---------------------------------
            if task.min_experience:
                if rec.experience_years >= task.min_experience:
                    score += 100 * EXPERIENCE_WEIGHT
                else:
                    exp_ratio = rec.experience_years / task.min_experience
                    score += exp_ratio * 100 * EXPERIENCE_WEIGHT

            # ---------------------------------
            # 3️⃣ EDUCATION MATCH
            # ---------------------------------
            if task.education_required and rec.highest_education:
                if task.education_required.lower() in rec.highest_education.lower():
                    score += 100 * EDUCATION_WEIGHT

            # ---------------------------------
            # 4️⃣ KEYWORD MATCH (JD vs Resume)
            # ---------------------------------
            if task.description and rec.pdf_text:
                jd_words = set(re.findall(r'\b\w+\b', task.description.lower()))
                resume_words = set(re.findall(r'\b\w+\b', rec.pdf_text.lower()))
                common_words = jd_words & resume_words

                if jd_words:
                    keyword_score = (len(common_words) / len(jd_words)) * 100
                    score += keyword_score * KEYWORD_WEIGHT

            # -------------------------------
            # ✅ Normalize score to 0-100
            # -------------------------------
            total_weight = SKILL_WEIGHT + EXPERIENCE_WEIGHT + EDUCATION_WEIGHT + KEYWORD_WEIGHT
            normalized_score = (score / (100 * total_weight)) * 100
            rec.score = round(normalized_score, 2)

            print(f"Raw score: {score:.2f}, Normalized score: {rec.score}")

    def normalize_skill(self,skill):
        skill = skill.strip().lower()

        # map variations
        if skill in SKILL_MAP:
            skill = SKILL_MAP[skill]

        return skill

    def get_skill_ids(self, skills_list):

        Skill = self.env['skill.master']
        skill_ids = []
        seen = set()

        for skill in skills_list:

            skill_clean = self.normalize_skill(skill)

            if not skill_clean or skill_clean in seen:
                continue

            seen.add(skill_clean)

            # search case-insensitive
            record = Skill.search([('name', '=ilike', skill_clean)], limit=1)

            if not record:
                record = Skill.create({
                    'name': skill_clean.title()
                })

            skill_ids.append(record.id)

        return skill_ids

    def clean_sender_name(sender_name):
        # Remove email part in <>
        name_part = re.sub(r'<.*?>', '', sender_name)
        # Remove surrounding quotes and whitespace
        return name_part.replace('"', '').strip()

    def clean_email_body(self,body):
        if not body:
            return ""
        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', '', body)
        # Convert HTML entities to normal characters
        text = unescape(text)
        # Remove excessive spaces and line breaks
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        subject = msg_dict.get('subject', '') or ''
        body = msg_dict.get('body', '') or ''
        email = msg_dict.get('email_from', '') or ''
        sender_name = msg_dict.get('from', '') or email

        if not email or 'noreply' in email.lower():
            return self.browse()

        attachments = msg_dict.get('attachments', []) or []

        resume_file = False
        resume_filename = False
        resume_ext = ('.pdf', '.doc', '.docx')

        # -------------------------
        # Detect Resume Attachment
        # -------------------------
        for attachment in attachments:
            filename = attachment[0]
            filedata = attachment[1]

            if filename and filename.lower().endswith(resume_ext):
                resume_file = filedata
                resume_filename = filename
                break

        if not resume_file:
            print("No resume attachment found")
            return self.browse()

        job = False
        resume_data = {}

        # -------------------------
        # Save attachment temporarily for parsing
        # -------------------------
        try:
            suffix = os.path.splitext(resume_filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(resume_file)
                tmp_path = tmp_file.name

            # Use sender_name as manual input seed
            manual_input = sender_name
            resume_data = parse_resume(tmp_path, manual_input)

            # Remove temp file
            os.unlink(tmp_path)
        except Exception as e:
            print("Resume parse error:", e)
            resume_data = {}

        # -------------------------
        # Extract fields with fallback
        # -------------------------
        name = resume_data.get("name") or self.clean_sender_name(sender_name)
        phone = resume_data.get("mobile") or ""
        linkedin_url = resume_data.get("linkedin") or ""
        github_url = resume_data.get("github_url") or ""
        email_from_resume = resume_data.get("email")
        education = resume_data.get("education") or ""
        highest_education = resume_data.get("highest_education") or ""
        pdf_text = resume_data.get("pdf_text") or ""
        if not email_from_resume:
            email_from_resume = email
        skills = resume_data.get("skills", [])
        experience_years = resume_data.get("total_experience_years", [])

        # Fallback Mobile from Email Body
        if not phone:
            phone_match = re.search(r'\+?\d[\d\s\-]{8,15}', body)
            if phone_match:
                phone = phone_match.group().strip()

        # -------------------------
        # Detect Job From Email
        # -------------------------
        content = (subject + " " + body).lower()
        jobs = self.env['project.task'].search([])
        for j in jobs:
            if j.name and j.name.lower() in content:
                job = j
                break

        # Fallback Job
        if not job:
            job = self.env['project.task'].search(
                [('name', 'ilike', 'general')],
                limit=1
            )

        # -------------------------
        # Create Applicant
        # -------------------------
        values = {
            'name': name,
            'email': email_from_resume,
            'description': self.clean_email_body(body),
            'mobile': phone,
            'task_id': job.id if job else False,
        }

        skill_ids = self.get_skill_ids(skills)

        applicant = super(AtsApplicant, self).message_new(msg_dict, values)
        applicant.write({
            'skill_ids': [(6, 0, skill_ids)],
            'linkedin_url': linkedin_url,
            'github_url': github_url,
            'highest_education': highest_education,
            'education': education,
            'pdf_text': pdf_text,
            'experience_years': experience_years,
        })

        # -------------------------
        # Save Resume
        # -------------------------
        if applicant and resume_file:
            applicant.write({
                'resume': base64.b64encode(resume_file),
                'resume_filename': resume_filename,
                'email': email_from_resume,
            })

        return applicant

    def _compute_stage_status_str(self):
        for rec in self:
            if rec.stage_id:
                if getattr(rec.stage_id, 'is_hired', False):
                    rec.stage_status_str = 'Hired'
                elif getattr(rec.stage_id, 'is_rejected', False):
                    rec.stage_status_str = 'Rejected'
                else:
                    rec.stage_status_str = 'In Progress'
            else:
                rec.stage_status_str = 'In Progress'

    @api.depends('invoice_line_id')
    def _compute_invoice_status(self):
        for rec in self.sudo():
            if rec.invoice_line_id:
                rec.invoice_status = 'invoiced'
            else:
                rec.invoice_status = 'not_invoiced'

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