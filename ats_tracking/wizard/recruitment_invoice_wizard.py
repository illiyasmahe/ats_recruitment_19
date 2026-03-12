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
from odoo.exceptions import UserError, ValidationError


class RecruitmentInvoiceWizard(models.TransientModel):
    _name = "recruitment.invoice.wizard"
    _description = "Recruitment Invoice Wizard"

    task_id = fields.Many2one(
        'project.task',
        string="Job Position",
        required=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string="Customer",
        required=True
    )

    qty = fields.Integer(
        string="Positions to Invoice",
        required=True
    )

    price_unit = fields.Float(
        string="Unit Price"
    )

    total_amount = fields.Float(
        string="Total Amount"
    )

    available_positions = fields.Integer(
        string="Available Positions",
        related="task_id.invoiceable_positions",
        readonly=True
    )

    applicant_ids = fields.Many2many(
        'ats.applicant',
        string="Applicants",
        domain="[('task_id','=',task_id)]",
        required=True
    )

    @api.constrains('applicant_ids', 'qty')
    def _check_applicant_qty(self):
        for rec in self:
            if rec.qty and len(rec.applicant_ids) != rec.qty:
                raise ValidationError(
                    f"You selected {len(rec.applicant_ids)} applicant(s), "
                    f"but Positions to Invoice is {rec.qty}. "
                    "Both must be equal."
                )

    @api.onchange('total_amount', 'qty')
    def _onchange_total(self):
        if self.total_amount and self.qty:
            self.price_unit = self.total_amount / self.qty

    @api.onchange('price_unit', 'qty')
    def _onchange_price(self):
        if self.price_unit and self.qty:
            self.total_amount = self.price_unit * self.qty

    @api.constrains('price_unit', 'total_amount')
    def _check_price(self):
        for rec in self:
            if rec.price_unit <= 0 and rec.total_amount <= 0:
                raise ValidationError("Price must be greater than zero.")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        product = self.env['product.template'].search([
            ('is_recruitment_service', '=', True)
        ], limit=1).product_variant_id

        if product:
            res['price_unit'] = product.list_price

        return res

    def action_create_invoice(self):

        self.ensure_one()

        if self.qty <= 0:
            raise UserError("Enter a valid quantity.")

        if self.qty > self.available_positions:
            raise UserError("Quantity exceeds available positions.")

        product = self.env['product.template'].search([
            ('is_recruitment_service', '=', True)
        ], limit=1).product_variant_id

        if not product:
            raise UserError("Recruitment Service product not found.")

        analytic_id = self.task_id.project_id.account_id.id
        lines = []

        for applicant in self.applicant_ids:
            lines.append((0, 0, {
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'name': f"{self.task_id.name} - {applicant.name}",
                'analytic_distribution': {
                    analytic_id: 100.0,
                },
                'quantity': 1,
                'price_unit': self.price_unit,
                'applicant_id': applicant.id,
                'job_position_id': self.task_id.id,
            }))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'ref': f"Recruitment {self.task_id.name}",
            'invoice_line_ids': lines
        })
        # LINK APPLICANTS AFTER LINES CREATED
        for line in invoice.invoice_line_ids:
            if line.applicant_id:
                line.applicant_id.invoice_line_id = line.id
        invoice.action_post()

        # update invoiced count
        self.task_id.invoiced_positions += self.qty

        # append invoice
        self.task_id.write({
            'invoice_ids': [(4, invoice.id)]
        })