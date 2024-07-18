from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError, AccessError
import json
from odoo.tools.misc import formatLang, format_date, get_lang, groupby


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    exchange_rate = fields.Float(string='Exchange Rate', digits=(12, 6), store=True, copy=False, default=1.00)
    foreign_currency_id = fields.Many2one("res.currency", string='Currency',
                                          default=lambda self: self.env.company.currency_id)
    exchange_total_amount = fields.Monetary("Exchange Amount Total", compute='compute_exchange_total_amount', store=True)

    @api.depends('amount_total', 'foreign_currency_id', 'exchange_rate', 'invoice_line_ids.product_id')
    def compute_exchange_total_amount(self):
        for order in self:
            if order.foreign_currency_id != order.currency_id:
                order.exchange_total_amount = order.amount_total * order.exchange_rate
            else:
                order.exchange_total_amount = 0.00

    @api.onchange('exchange_rate', 'foreign_currency_id')
    def onchange_check_exchange_rate(self):
        if self.exchange_rate < 0:
            raise ValidationError("Warning, Exchange Rate Should Be Greater than Zero")

    @api.onchange('foreign_currency_id')
    def _onchange_foreign_currency_id(self):
        if self.foreign_currency_id:
            currency = self.env['res.currency']
            rate = currency._get_conversion_rate(from_currency=self.foreign_currency_id, to_currency=self.currency_id or self.company_id.currency_id, company=self.company_id, date=self.invoice_date or fields.Date.today())
            self.exchange_rate = rate

    @api.depends_context('lang')
    @api.depends('line_ids.amount_currency', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id',
                 'currency_id', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals_json(self):
        super(AccountMoveInherit, self)._compute_tax_totals_json()
        for move in self:
            if move.tax_totals_json and move.move_type in ('out_invoice', 'out_refund', 'out_receipt'):
                tax_totals = json.loads(move.tax_totals_json)
                tax_totals['exchange_total_amount'] = move.exchange_total_amount
                tax_totals['formatted_exchange_total_amount'] = formatLang(self.env, move.exchange_total_amount,
                                                                           currency_obj=move.currency_id)
                move.tax_totals_json = json.dumps(tax_totals)