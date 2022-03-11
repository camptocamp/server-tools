# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

# This script is not meant to be used as is.
# Add it in your module in order to add the `jsonified_data` column
# before the installation of the module, in order to avoid the computation,
# which might be slow.


def pre_init_hook(cr):
    query = """
        ALTER TABLE model ADD COLUMN jsonified_data TEXT;
    """
    cr.execute(query)
