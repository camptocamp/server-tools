# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import logging

from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Migrating conditional image's model names to model records")
    env = api.Environment(cr, SUPERUSER_ID, {})
    conditional_images = env["conditional.image"].search([("model_name", "!=", False)])
    ir_model = env["ir.model"]
    for image in conditional_images:
        model = ir_model.search([("model", "=", image.model_name)])
        if not model:
            _logger.error(f"A conditional images missed a model: {image.name}")
        image.model_id = model

    # Removes model_name which is not stored anymore
    openupgrade.drop_columns(cr, [("conditional_image", "model_name")])
