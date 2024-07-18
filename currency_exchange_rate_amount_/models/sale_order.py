from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError, AccessError, UserError
import json
from odoo.tools.misc import formatLang, format_date, get_lang, groupby


class SalesOrder(models.Model):
    _inherit = 'sale.order'

    exchange_rate = fields.Float(string='Exchange Rate', digits=(12, 6), store=True, copy=False, default=1.00)
    foreign_currency_id = fields.Many2one("res.currency", string='Currency',
                                          default=lambda self: self.env.company.currency_id)
    exchange_total_amount = fields.Monetary("Exchange Amount Total", compute='compute_exchange_total_amount',default=0.00)

    @api.depends('amount_total', 'foreign_currency_id', 'exchange_rate', 'order_line.product_id', 'order_line.product_uom_qty', 'order_line.price_unit')
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
            rate = currency._get_conversion_rate(from_currency=self.foreign_currency_id, to_currency=self.currency_id or self.company_id.currency_id, company=self.company_id, date=self.date_order or fields.Date.today())
            self.exchange_rate = rate

    @api.depends_context('lang')
    @api.depends('order_line.tax_id', 'order_line.price_unit', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals_json(self):
        super(SalesOrder, self)._compute_tax_totals_json()
        for order in self:
            if order.tax_totals_json:
                tax_totals = json.loads(order.tax_totals_json)
                tax_totals['exchange_total_amount'] = order.exchange_total_amount
                tax_totals['formatted_exchange_total_amount'] = formatLang(self.env, order.exchange_total_amount, currency_obj=order.currency_id)
                order.tax_totals_json = json.dumps(tax_totals)


class SaleAdvanceInherit(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        res = super(SaleAdvanceInherit, self).create_invoices()
        domain_list = res.get('domain', [])
        if domain_list[0][0] == 'id':
            invoice_id = self.env['account.move'].browse(domain_list[0][2][-1])
        else:
            invoice_id = self.env['account.move'].browse(res['res_id'])

        sale = self.env['sale.order'].search([('name', '=', invoice_id.invoice_origin)])
        update_inv = {
            'foreign_currency_id': sale.foreign_currency_id,
            'exchange_rate': sale.exchange_rate,
        }
        invoice_id.write(update_inv)
        return res
