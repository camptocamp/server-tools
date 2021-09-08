# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from functools import wraps


def orderable(method):
    """This decorator executes the method as usual.
    Once it's done, it tries to find and execute method overloads sorted by sequence.
    """

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        res = method(self, *args, **kwargs)

        overloads = self.env["method.overload"].search(
            [
                ("method_name", "=", method.__name__),
                ("method_model", "=", self._name),
            ], order="sequence asc"
        )

        for overload in overloads:
            res = overload.run(self, res)

        return res

    return wrapper
