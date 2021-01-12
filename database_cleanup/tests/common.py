# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase, at_install, post_install


# Use post_install to get all models loaded more info: odoo/odoo#13458
@at_install(False)
@post_install(True)
class Common(TransactionCase):
    def setUp(self):
        super(Common, self).setUp()
        self.module = None
        self.model = None
        # Create one property for tests
        partner_name_field_id = self.env["ir.model.fields"].search(
            [("name", "=", "name"), ("model_id.model", "=", "res.partner")], limit=1
        )
        self.env["ir.property"].create(
            {
                "fields_id": partner_name_field_id.id,
                "type": "char",
                "value_text": "My default partner name",
            }
        )

    def tearDown(self):
        super(Common, self).tearDown()
        with self.registry.cursor() as cr2:
            # Release blocked tables with pending deletes
            self.env.cr.rollback()
            if self.module:
                cr2.execute(
                    "DELETE FROM ir_module_module WHERE id=%s", (self.module.id,)
                )
            if self.model:
                cr2.execute("DELETE FROM ir_model WHERE id=%s", (self.model.id,))
            cr2.commit()
