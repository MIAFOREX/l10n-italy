# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Associazione Odoo Italia
#    (<http://www.odoo-italia.org>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models, api, _, exceptions, workflow
import time
import openerp.addons.decimal_precision as dp
# from openerp import netsvc


class riba_list(models.Model):

    @api.multi
    def _get_acceptance_move_ids(self):
        res = {}
        for list in self:
            move_ids = []
            for line in list.line_ids:
                if (line.acceptance_move_id and
                        line.acceptance_move_id.id not in move_ids):
                    move_ids.append(line.acceptance_move_id.id)
            res[list.id] = move_ids
        return res

    @api.multi
    def _get_unsolved_move_ids(self):
        res = {}
        for list in self:
            move_ids = []
            for line in list.line_ids:
                if (line.unsolved_move_id and
                        line.unsolved_move_id.id not in move_ids):
                    move_ids.append(line.unsolved_move_id.id)
            res[list.id] = move_ids
        return res

    @api.multi
    def _get_payment_ids(self):
        res = {}
        for list in self:
            move_line_ids = []
            for line in list.line_ids:
                for payment in line.payment_ids:
                    if payment.id not in move_line_ids:
                        move_line_ids.append(payment.id)
            res[list.id] = move_line_ids
        return res

    _name = 'riba.list'
    _description = 'Riba list'

    name = fields.Char(
        'Reference', size=128, required=True, readonly=True,
        states={'draft': [('readonly', False)]},
        default=(lambda self: self.env['ir.sequence'].get('riba.list')))
    config_id = fields.Many2one(
        'riba.configuration', string='Configuration', select=True,
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        help='Riba configuration to be used')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('accepted', 'Accepted'),
        ('accredited', 'Accredited'),
        ('paid', 'Paid'),
        ('unsolved', 'Unsolved'),
        ('cancel', 'Canceled')], 'State', select=True, readonly=True,
        default='draft')
    line_ids = fields.One2many(
        'riba.list.line', 'list_id', 'Riba deadlines', readonly=True,
        states={'draft': [('readonly', False)]})
    user_id = fields.Many2one(
        'res.users', 'User', required=True, readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user,)
    date_created = fields.Date(
        'Creation date', readonly=True,
        default=lambda self: fields.Date.context_today(self))
    date_accepted = fields.Date('Acceptance date', readonly=True)
    date_accreditation = fields.Date('Accreditation date', readonly=True)
    date_paid = fields.Date('Paid date', readonly=True)
    date_unsolved = fields.Date('Unsolved date', readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company', required=True, readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get(
            'riba.list'))
    acceptance_move_ids = fields.Many2many(
        compute='_get_acceptance_move_ids', string="Acceptance Entries")
    accreditation_move_id = fields.Many2one(
        'account.move', 'Accreditation Entry', readonly=True)
    payment_ids = fields.Many2many(
        'account.move.line', compute='_get_payment_ids', string='Payments')
    unsolved_move_ids = fields.Many2many(
        compute='_get_unsolved_move_ids', string="Unsolved Entries")
    type = fields.Selection(
        string="Type", related='config_id.type', readonly=True)
    registration_date = fields.Date(
        'Registration Date',
        states={'draft': [('readonly', False)],
                'cancel': [('readonly', False)], },
        select=True, readonly=True,
        required=True,
        default=lambda self: fields.Date.context_today(self),
        help="Keep empty to use the current date")

    def unlink(self, cr, uid, ids, context=None):
        for list in self.browse(cr, uid, ids, context=context):
            if list.state not in ('draft',  'cancel'):
                raise exceptions.Warning(
                    _('Error'),
                    _('List %s is in state %s. You can only delete documents \
in state draft or canceled') % (list.name, list.state))
        super(riba_list, self).unlink(cr, uid, ids, context=context)
        return True

    def confirm(self, cr, uid, ids, context=None):
        line_pool = self.pool.get('riba.list.line')
        for list in self.browse(cr, uid, ids, context=context):
            line_pool.confirm(cr, uid, [line.id for line in list.line_ids],
                              context=context)
        return True

    def riba_new(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'draft',
            }, context=context)
        return True

    def riba_cancel(self, cr, uid, ids, context=None):
        for list in self.browse(cr, uid, ids, context=context):
            # TODO remove ervery other move
            for line in list.line_ids:
                if line.acceptance_move_id:
                    line.acceptance_move_id.unlink()
                if line.unsolved_move_id:
                    line.unsolved_move_id.unlink()
            if list.accreditation_move_id:
                list.accreditation_move_id.unlink()
        self.write(cr, uid, ids, {
            'state': 'cancel',
            }, context=context)
        return True

    def riba_accepted(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'accepted',
            'date_accepted': fields.Date.context_today(self),
            }, context=context)
        return True

    def riba_accredited(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'accredited',
            'date_accreditation': fields.Date.context_today(self),
            }, context=context)
        for list in self.browse(cr, uid, ids, context=context):
            for line in list.line_ids:
                line.write({'state': 'accredited'})
        return True

    def riba_paid(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'paid',
            'date_paid': fields.Date.context_today(self),
            }, context=context)
        return True

    def riba_unsolved(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'unsolved',
            'date_unsolved': fields.Date.context_today(self),
            }, context=context)
        return True

    def test_accepted(self, cr, uid, ids, *args):
        for list in self.browse(cr, uid, ids):
            for line in list.line_ids:
                if line.state != 'confirmed':
                    return False
        return True

    def test_unsolved(self, cr, uid, ids, *args):
        for list in self.browse(cr, uid, ids):
            for line in list.line_ids:
                if line.state != 'unsolved':
                    return False
        return True

    def test_paid(self, cr, uid, ids, *args):
        for list in self.browse(cr, uid, ids):
            for line in list.line_ids:
                if line.state != 'paid':
                    return False
        return True

    def action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'})
        # wf_service = netsvc.LocalService("workflow")
        for list_id in ids:
            workflow.trg_delete(uid, 'riba.list', list_id, cr)
            workflow.trg_create(uid, 'riba.list', list_id, cr)
        return True


class riba_list_line(models.Model):

    @api.multi
    def _get_line_values(self):
        res = {}
        for line in self:
            res[line.id] = {}
            res[line.id]['amount'] = 0.0
            res[line.id]['invoice_date'] = ''
            res[line.id]['invoice_number'] = ''
            for move_line in line.move_line_ids:
                res[line.id]['amount'] += move_line.amount
                if not res[line.id]['invoice_date']:
                    res[line.id]['invoice_date'] = str(
                        move_line.move_line_id.invoice.date_invoice)
                else:
                    res[line.id]['invoice_date'] += ', ' + str(
                        move_line.move_line_id.invoice.date_invoice)
                if not res[line.id]['invoice_number']:
                    res[line.id]['invoice_number'] = str(
                        move_line.move_line_id.invoice.internal_number)
                else:
                    res[line.id]['invoice_number'] += ', ' + str(
                        move_line.move_line_id.invoice.internal_number)
        return res

    def _reconciled(self, cr, uid, ids, name, args, context=None):
        #wf_service = netsvc.LocalService("workflow")
        res = {}
        for id in ids:
            res[id] = self.test_paid(cr, uid, [id])
            if res[id]:
                self.write(cr, uid, id, {'state': 'paid'}, context=context)
                workflow.trg_validate(
                    uid, 'riba.list',
                    self.browse(cr, uid, id).list_id.id, 'paid', cr)
        return res

    def move_line_id_payment_gets(self, cr, uid, ids, *args):
        res = {}
        if not ids:
            return res
        cr.execute('SELECT list_line.id, l.id '
                   'FROM account_move_line l '
                   'LEFT JOIN riba_list_line list_line ON '
                   '(list_line.acceptance_move_id=l.move_id) '
                   'WHERE list_line.id IN %s '
                   'AND l.account_id=list_line.acceptance_account_id',
                   (tuple(ids),))
        for r in cr.fetchall():
            res.setdefault(r[0], [])
            res[r[0]].append(r[1])
        return res

    # return the ids of the move lines which has the same account than the
    # statement whose id is in ids
    def move_line_id_payment_get(self, cr, uid, ids, *args):
        if not ids:
            return []
        result = self.move_line_id_payment_gets(cr, uid, ids, *args)
        return result.get(ids[0], [])

    def test_paid(self, cr, uid, ids, *args):
        res = self.move_line_id_payment_get(cr, uid, ids)
        if not res:
            return False
        ok = True
        for id in res:
            cr.execute(
                'select reconcile_id from account_move_line where id=%s',
                (id,))
            ok = ok and bool(cr.fetchone()[0])
        return ok

    def _get_riba_line_from_move_line(self, cr, uid, ids, context=None):
        move = {}
        for line in self.pool['account.move.line'].browse(cr, uid, ids,
                                                          context=context):
            if line.reconcile_partial_id:
                for line2 in line.reconcile_partial_id.line_partial_ids:
                    move[line2.move_id.id] = True
            if line.reconcile_id:
                for line2 in line.reconcile_id.line_id:
                    move[line2.move_id.id] = True
        line_ids = []
        if move:
            line_ids = self.pool.get('riba.list.line').search(
                cr, uid, [('acceptance_move_id', 'in', move.keys())],
                context=context)
        return line_ids

    def _get_line_from_reconcile(self, cr, uid, ids, context=None):
        move = {}
        for r in self.pool['account.move.reconcile'].browse(cr, uid, ids,
                                                            context=context):
            for line in r.line_partial_ids:
                move[line.move_id.id] = True
            for line in r.line_id:
                move[line.move_id.id] = True
        line_ids = []
        if move:
            line_ids = self.pool.get('riba.list.line').search(
                cr, uid, [('acceptance_move_id', 'in', move.keys())],
                context=context)
        return line_ids

    @api.multi
    def _compute_lines(self):
        result = {}
        for riba_line in self:
            src = []
            lines = []
            if riba_line.acceptance_move_id:
                for m in riba_line.acceptance_move_id.line_id:
                    temp_lines = []
                    if m.reconcile_id and m.credit == 0.0:
                        temp_lines = map(
                            lambda x: x.id, m.reconcile_id.line_id)
                    elif m.reconcile_partial_id and m.credit == 0.0:
                        temp_lines = map(
                            lambda x: x.id,
                            m.reconcile_partial_id.line_partial_ids)
                    lines += [x for x in temp_lines if x not in lines]
                    src.append(m.id)

            lines = filter(lambda x: x not in src, lines)
            result[riba_line.id] = lines
        return result

    # TODO estendere la account_due_list per visualizzare e filtrare in base alle riba ?
    _name = 'riba.list.line'
    _description = 'Riba details'
    _rec_name = 'sequence'

    sequence = fields.Integer('Number')
    move_line_ids = fields.One2many(
        'riba.list.move.line', 'riba_line_id', string='Credit move lines')
    acceptance_move_id = fields.Many2one(
        'account.move', string='Acceptance Entry', readonly=True)
    unsolved_move_id = fields.Many2one(
        'account.move', string='Unsolved Entry', readonly=True)
    acceptance_account_id = fields.Many2one(
        'account.account', string='Acceptance Account')
    amount = fields.Float(
        compute='_get_line_values', string="Amount")
    bank_id = fields.Many2one('res.partner.bank', string='Debitor Bank')
    iban = fields.Char(
        related='bank_id.iban', string='IBAN', store=False,
        readonly=True)
    list_id = fields.Many2one(
        'riba.list', string='List', required=True, ondelete='cascade')
    partner_id = fields.Many2one(
        'res.partner', string="Cliente", readonly=True)
    invoice_date = fields.Char(
        compute='_get_line_values', string="Invoice Date", size=256)
    invoice_number = fields.Char(
        compute='_get_line_values', string="Invoice Number", size=256)
    due_date = fields.Date("Due date", readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('accredited', 'Accredited'),
        ('paid', 'Paid'),
        ('unsolved', 'Unsolved'),
        ], 'State', select=True, readonly=True, track_visibility='onchange')
    reconciled = fields.Boolean(
        compute='_reconciled', string='Paid/Reconciled',
        store=True,
        help="It indicates that the line has been paid and the journal \
entry of the line has been reconciled with one or several journal entries of \
payment.")
    """
    store={
        'riba.list.line': (lambda self, cr, uid, ids, c={}: ids,
                           ['acceptance_move_id'], 50),
        'account.move.line': (_get_riba_line_from_move_line, None, 50),
        'account.move.reconcile': (_get_line_from_reconcile, None, 50),
    },
    """
    payment_ids = fields.Many2many(
        'account.move.line', compute='_compute_lines', string='Payments')
    type = fields.Char(
        relation='list_id.type', size=32, string='Type', readonly=True)

    def confirm(self, cr, uid, ids, context=None):
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        #wf_service = netsvc.LocalService("workflow")
        for line in self.browse(cr, uid, ids, context=context):
            journal = line.list_id.config_id.acceptance_journal_id
            total_credit = 0.0
            move_id = move_pool.create(cr, uid, {
                'ref': 'Ri.Ba. %s - line %s' % (line.list_id.name,
                                                line.sequence),
                'journal_id': journal.id,
                'date': line.list_id.registration_date,
                }, context=context)
            to_be_reconciled = []
            for riba_move_line in line.move_line_ids:
                total_credit += riba_move_line.amount
                move_line_id = move_line_pool.create(cr, uid, {
                    'name': riba_move_line.move_line_id.invoice.number,
                    'partner_id': line.partner_id.id,
                    'account_id': riba_move_line.move_line_id.account_id.id,
                    'credit': riba_move_line.amount,
                    'debit': 0.0,
                    'move_id': move_id,
                    }, context=context)
                to_be_reconciled.append([move_line_id,
                                         riba_move_line.move_line_id.id])
            move_line_pool.create(cr, uid, {
                'name': 'Ri.Ba. %s - line %s' % (line.list_id.name,
                                                 line.sequence),
                'account_id': (
                    line.acceptance_account_id.id or
                    line.list_id.config_id.acceptance_account_id.id
                    # in questo modo se la riga non ha conto accettazione
                    # viene prelevato il conto in configuration riba
                    ),
                'partner_id': line.partner_id.id,
                'date_maturity': line.due_date,
                'credit': 0.0,
                'debit': total_credit,
                'move_id': move_id,
                }, context=context)
            move_pool.post(cr, uid, [move_id], context=context)
            for reconcile_ids in to_be_reconciled:
                move_line_pool.reconcile_partial(cr, uid, reconcile_ids,
                                                 context=context)
            line.write({
                'acceptance_move_id': move_id,
                'state': 'confirmed',
                })
            workflow.trg_validate(
                uid, 'riba.list', line.list_id.id, 'accepted', cr)
        return True


class riba_list_move_line(models.Model):

    _name = 'riba.list.move.line'
    _description = 'Riba details'
    _rec_name = 'amount'

    amount = fields.Float(
        'Amount', digits_compute=dp.get_precision('Account'))
    move_line_id = fields.Many2one(
        'account.move.line', string='Credit move line')
    riba_line_id = fields.Many2one(
        'riba.list.line', string='List line', ondelete='cascade')