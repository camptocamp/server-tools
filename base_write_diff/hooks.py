# Copyright 2025 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
from logging import getLogger

from odoo import models
from odoo.tools.misc import frozendict

_logger = getLogger(__name__)


def patch_base_model_write():
    """Patch ``BaseModel.write()``

    We want to make sure that the context key is intercepted at the last possible step
    before the record is updated, to prevent other overrides from adding new values to
    the dictionary *after* it's been cleaned up by ``_get_write_diff_values()`` and
    *before* the base method is called
    """
    _logger.info("post_load_hook(): patching ``BaseModel.write()``...")
    original_write = models.BaseModel.write

    def patched_write(self, vals: dict):
        if not (self and vals and self.env.context.get("write_use_diff_values")):
            return original_write(self, vals)
        recs_grouped = defaultdict(lambda: self.browse())
        for record in self:
            recs_grouped[frozendict(record._get_write_diff_values(vals))] += record
        for diff_vals, recs in recs_grouped.items():
            if diff_vals:  # Don't trigger ``write()`` if there is nothing to update
                original_write(recs, dict(diff_vals))
        return True

    models.BaseModel.write = patched_write


def post_load_hook():
    patch_base_model_write()
