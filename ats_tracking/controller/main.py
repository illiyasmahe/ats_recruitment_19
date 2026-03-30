from odoo import http
from odoo.http import request

class ApplicantController(http.Controller):

    @http.route('/applicant/accept/<int:applicant_id>', type='http', auth='public', website=True)
    def accept(self, applicant_id, **kwargs):
        applicant = request.env['ats.applicant'].sudo().browse(applicant_id)
        if not applicant:
            return request.render('ats_tracking.applicant_invalid_page')

        if applicant.mail_status != 'pending':
            return request.render('ats_tracking.applicant_expired_page')

        applicant.sudo().write({'mail_status': 'accepted'})
        return request.render('ats_tracking.applicant_accept_page')

    @http.route('/applicant/reject/<int:applicant_id>', type='http', auth='public', website=True)
    def reject(self, applicant_id, **kwargs):
        applicant = request.env['ats.applicant'].sudo().browse(applicant_id)
        if not applicant:
            return request.render('ats_tracking.applicant_invalid_page')

        if applicant.mail_status != 'pending':
            return request.render('ats_tracking.applicant_expired_page')

        applicant.sudo().write({'mail_status': 'rejected'})
        return request.render('ats_tracking.applicant_reject_page')