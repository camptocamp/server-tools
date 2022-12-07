# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from openupgradelib.openupgrade import (
    drop_columns,
    rename_columns,
    rename_fields,
    rename_models,
    rename_tables,
)

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    rename_models(cr, [("image", "conditional.image")])
    rename_tables(cr, [("image", "conditional_image")])
    # Only migrate field image to image_1920 as other fields are related to image_1920
    env = api.Environment(cr, SUPERUSER_ID, {})
    rename_fields(
        env, [("conditional.image", "conditional_image", "image", "image_1920")]
    )
    rename_columns(cr, {"conditional_image": [("image", "image_1920")]})
    drop_columns(
        cr,
        [("conditional_image", "image_medium"), ("conditional_image", "image_small")],
    )
