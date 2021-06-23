# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common import Common


class TestCleanupPurgeLineColumn(Common):
    def setUp(self):
        super(TestCleanupPurgeLineColumn, self).setUp()
        # create a nonexistent model
        self.model = self.env["ir.model"].create(
            {
                "name": "Database cleanup test model",
                "model": "x_database.cleanup.test.model",
            }
        )
        self.env.cr.execute(
            "insert into ir_attachment (name, res_model, res_id, type) values "
            "('test attachment', 'database.cleanup.test.model', 42, 'binary')"
        )
        self.env.registry.models.pop("x_database.cleanup.test.model")

    def test_empty_model(self):
        wizard = self.env["cleanup.purge.wizard.model"].create({})
        wizard.purge_all()
        # must be removed by the wizard
        self.assertFalse(
            self.env["ir.model"].search(
                [
                    ("model", "=", "x_database.cleanup.test.model"),
                ]
            )
        )
