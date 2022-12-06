# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from openupgradelib import rename_fields, rename_models


def migrate(cr, version):

    rename_models([("image", "conditional.image")])
    # Only migrate field image to image_1920 as other fields are related to image_1920
    rename_fields([("conditional.image", "conditional_image", "image", "image_1920")])
