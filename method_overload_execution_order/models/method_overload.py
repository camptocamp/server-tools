# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging
from importlib import import_module

from odoo import fields, models

_logger = logging.getLogger(__name__)


class MethodOverload(models.Model):
    _name = "method.overload"
    _description = "Representation of a method overload"

    method_name = fields.Char(string="Name", help="The name of the overloaded method",)
    method_model = fields.Char(string="Model", help="The name of the overridden model",)
    method_module = fields.Char(
        string="Module", help="The name of the module where the method is overloaded.",
    )
    method_filename = fields.Char(
        string="Filename",
        help=(
            "The name of the file (without extension) where the method is overloaded."
        ),
    )
    method_delegate_name = fields.Char(
        help=(
            "The name of the method that will be used to "
            "alter the output of the overloaded method."
        )
    )
    method_class_name = fields.Char(
        string="Class Name", help="The class name, as written in the python file."
    )
    sequence = fields.Integer()

    _sql_constraints = [
        (
            "unique_method_per_model_per_module",
            "unique(method_name, method_model, method_module)",
            (
                "There can be only one method with a given name "
                "in a model, for a given module"
            ),
        ),
        (
            "unique_delegate_method_per_method",
            "unique(method_name, method_model, method_delegate_name)",
            "There can be only one delegate method for an overridden method.",
        ),
    ]

    def _get_module_path(self):
        return f"odoo.addons.{self.method_module}.models.{self.method_filename}"

    def _import_module(self):
        try:
            module_path = self._get_module_path()
            return import_module(module_path)
        except ImportError:
            _logger.error("Couldn't import `{module_path}`")
            return False

    def _import_class_from_module(self, module):
        klass = getattr(module, self.method_class_name, None)
        if not klass:
            _logger.error(
                "No class named {self.method_class_name} found in module {module}"
            )
        return klass

    def _get_method_from_class(self, klass):
        meth = getattr(klass, self.method_delegate_name, None)
        if not meth:
            _logger.error(
                "Couldn't find method {overload.method_delegate_name} "
                "for class {klass} in module {module_path}"
            )
        return meth

    def run(self, record, result):
        """Tries to find the delegate method, and execute it."""
        # Try to import the module
        module = self._import_module()
        if not module:
            return result
        # Try to retrieve the class from the module
        klass = self._import_class_from_module(module)
        if not klass:
            return result
        # Try to retrieve the `delegate method` from the class
        meth = self._get_method_from_class(klass)
        if not meth:
            return result
        # Finally, return altered result
        return meth(record, result)
