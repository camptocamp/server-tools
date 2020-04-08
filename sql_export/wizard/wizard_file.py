# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Akretion (<http://www.akretion.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from openerp.osv import fields, orm
from openerp.osv.orm import setup_modifiers
import StringIO
import base64
import datetime
from lxml import etree
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import uuid


class SqlFileWizard(orm.TransientModel):
    _name = "sql.file.wizard"
    _description = "Allow the user to save the file with sql request's data"

    _rec_name = 'file_name'

    _columns = {
        'file': fields.binary('File', readonly=True),
        'file_name': fields.char('File Name', readonly=True),
        'valid': fields.boolean(),
        'sql_export_id': fields.many2one('sql.export', required=True)
    }

    def fields_view_get(
            self, cr, uid, view_id=None, view_type='form', context=None,
            toolbar=False, submenu=False):
        """
        Display dinamicaly parameter fields depending on the sql_export.
        """
        res = super(SqlFileWizard, self).fields_view_get(cr, uid,
            view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)
        export_obj = self.pool['sql.export']
        if view_type == 'form':
            sql_export = export_obj.browse(
                cr, uid, context.get('active_id'), context=context)
            if sql_export.field_ids:
                eview = etree.fromstring(res['arch'])
                group = etree.Element(
                    'group', name="variables_group", colspan="4")
                toupdate_fields = []
                for field in sql_export.field_ids:
                    kwargs = {'name': "%s" % field.name}
                    toupdate_fields.append(field.name)
                    view_field = etree.SubElement(group, 'field', **kwargs)
                    setup_modifiers(view_field, self.fields_get(cr, uid, [field.name], context=context))

                res['fields'].update(self.fields_get(cr, uid, toupdate_fields, context=context))
                placeholder = eview.xpath(
                    "//separator[@string='variables_placeholder']")[0]
                placeholder.getparent().replace(
                    placeholder, group)
                res['arch'] = etree.tostring(eview, pretty_print=True)
        return res

    def export_sql(self, cr, uid, ids, context=None):

        today = datetime.datetime.now()
        today_tz = fields.datetime.context_timestamp(
            cr, uid, today, context=context)
        date = today_tz.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        output = StringIO.StringIO()


        wizard = self.browse(cr, uid, ids, context=context)[0]
        sql_export = wizard.sql_export_id
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        variable_dict = {}
        if sql_export.field_ids:
            for field in sql_export.field_ids:
                variable_dict[field.name] = wizard[field.name]
        if "%(company_id)s" in sql_export.query:
            variable_dict['company_id'] = user.company_id.id
        if "%(user_id)s" in sql_export.query:
            variable_dict['user_id'] = uid
        format_query = cr.mogrify(sql_export.query, variable_dict).decode('utf-8')
        query = "COPY (" + format_query + ")  TO STDOUT WITH " + \
                sql_export.copy_options
        name = 'export_query_%s' % uuid.uuid1().hex
        cr.execute("SAVEPOINT %s" % name)
        try:
            cr.copy_expert(query, output)
            output.getvalue()
            new_output = base64.b64encode(output.getvalue())
            output.close()
        finally:
            cr.execute("ROLLBACK TO SAVEPOINT %s" % name)
        wizard.write({
            'file': new_output,
            'file_name': sql_export.name + '_' + date + '.csv'
        })
        if not sql_export.valid:
            self.pool['sql.export'].write(cr, 1, [sql_export.id], {'valid': True}, context=context)
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sql.file.wizard',
            'res_id': wizard.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
            'nodestroy': True,
        }
