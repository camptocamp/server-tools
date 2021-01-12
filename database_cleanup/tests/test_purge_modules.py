# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.modules.registry import Registry
from odoo.tools import config

from .common import Common


class TestCleanupPurgeLineModule(Common):
    def setUp(self):
        super(TestCleanupPurgeLineModule, self).setUp()
        # create a nonexistent module
        self.module = self.env["ir.module.module"].create(
            {
                "name": "database_cleanup_test",
                "state": "to upgrade",
            }
        )

    def test_purge(self):
        wizard = self.env["cleanup.purge.wizard.module"].create({})
        # this reloads our registry, and we don't want to run tests twice
        # we also need the original registry for further tests, so save a
        # reference to it
        original_registry = Registry.registries[self.env.cr.dbname]
        config.options["test_enable"] = False
        wizard.purge_all()
        config.options["test_enable"] = True
        # must be removed by the wizard
        self.assertFalse(
            self.env["ir.module.module"].search(
                [
                    ("name", "=", "database_cleanup_test"),
                ]
            )
        )
        # reset afterwards
        Registry.registries[self.env.cr.dbname] = original_registry
