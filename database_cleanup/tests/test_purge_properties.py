# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common import Common


class TestCleanupPurgeLineProperty(Common):
    def setUp(self):
        super(TestCleanupPurgeLineProperty, self).setUp()
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

    def test_purge(self):
        # duplicate a property
        duplicate_property = self.env["ir.property"].search([], limit=1).copy()
        wizard = self.env["cleanup.purge.wizard.property"].create({})
        wizard.purge_all()
        self.assertFalse(duplicate_property.exists())
