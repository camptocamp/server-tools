# Copyright 2016 Therp BV <https://therp.nl>
# Copyright 2018 Tecnativa - Sergio Teruel
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
import ast

import astor
from lxml import etree

from odoo import api, models, tools


class UnquoteObject(str):
    def __getattr__(self, name):
        return UnquoteObject("{}.{}".format(self, name))

    def __repr__(self):
        return self

    def __call__(self, *args, **kwargs):
        return UnquoteObject(
            "%s(%s)"
            % (
                self,
                ",".join(
                    [
                        UnquoteObject(a if not isinstance(a, str) else "'%s'" % a)
                        for a in args
                    ]
                    + ["{}={}".format(UnquoteObject(k), v) for (k, v) in kwargs.items()]
                ),
            )
        )


class UnquoteEvalObjectContext(tools.misc.UnquoteEvalContext):
    def __missing__(self, key):
        return UnquoteObject(key)


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    @api.model
    def apply_inheritance_specs(self, source, specs_tree, pre_locate=lambda s: True):
        for specs, handled_by in self._iter_inheritance_specs(specs_tree):
            pre_locate(specs)
            source = handled_by(source, specs)
        return source

    @api.model
    def _iter_inheritance_specs(self, spec):
        if spec.tag == "data":
            for child in spec:
                for node, handler in self._iter_inheritance_specs(child):
                    yield node, handler
            return
        if spec.get("position") == "attributes":
            if all(not c.get("operation") for c in spec):
                yield spec, self._get_inheritance_handler(spec)
                return
            for child in spec:
                node = etree.Element(spec.tag, **spec.attrib)
                node.insert(0, child)
                yield node, self._get_inheritance_handler_attributes(child)
            return
        yield spec, self._get_inheritance_handler(spec)

    @api.model
    def _get_inheritance_handler(self, node):
        handler = super(IrUiView, self).apply_inheritance_specs
        if hasattr(self, "inheritance_handler_%s" % node.tag):
            handler = getattr(self, "inheritance_handler_%s" % node.tag)
        return handler

    @api.model
    def _get_inheritance_handler_attributes(self, node):
        handler = super(IrUiView, self).apply_inheritance_specs
        if hasattr(self, "inheritance_handler_attributes_%s" % node.get("operation")):
            handler = getattr(
                self, "inheritance_handler_attributes_%s" % node.get("operation")
            )
        return handler

    @api.model
    def inheritance_handler_attributes_python_dict(self, source, specs):
        """Implement
        <$node position="attributes">
            <attribute name="$attribute" operation="python_dict" key="$key">
                $keyvalue
            </attribute>
        </$node>"""
        node = self.locate_node(source, specs)
        for attribute_node in specs:
            str_dict = node.get(attribute_node.get("name")) or "{}"
            tree = ast.parse(str_dict)
            # Some checks to ensure ast is really a python expr with a dict
            assert len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr)
            assert isinstance(tree.body[0].value, ast.Dict)
            ast_dict = tree.body[0].value
            # Find the ast dict key
            key_id = next(
                (
                    i
                    for i, k in enumerate(ast_dict.keys)
                    if isinstance(k, ast.Str) and k.s == attribute_node.get("key")
                ),
                None,
            )
            # Update or create the key
            new_value = ast.parse(attribute_node.text.strip()).body[0].value
            if key_id:
                ast_dict.values[key_id] = new_value
            else:
                ast_dict.keys.append(ast.Str(attribute_node.get("key")))
                ast_dict.values.append(new_value)
            # Dump the ast back to source
            node.attrib[attribute_node.get("name")] = astor.to_source(
                tree, pretty_source=lambda s: "".join(s).strip()
            )
        return source

    @api.model
    def inheritance_handler_attributes_list_add(self, source, specs):
        """Implement
        <$node position="attributes">
            <attribute name="$attribute" operation="list_add">
                $new_value
            </attribute>
        </$node>"""
        node = self.locate_node(source, specs)
        for attribute_node in specs:
            attribute_name = attribute_node.get("name")
            old_value = node.get(attribute_name) or ""
            new_value = old_value + "," + attribute_node.text
            node.attrib[attribute_name] = new_value
        return source

    @api.model
    def inheritance_handler_attributes_list_remove(self, source, specs):
        """Implement
        <$node position="attributes">
            <attribute name="$attribute" operation="list_remove">
                $value_to_remove
            </attribute>
        </$node>"""
        node = self.locate_node(source, specs)
        for attribute_node in specs:
            attribute_name = attribute_node.get("name")
            old_values = (node.get(attribute_name) or "").split(",")
            remove_values = attribute_node.text.split(",")
            new_values = [x for x in old_values if x not in remove_values]
            node.attrib[attribute_name] = ",".join([_f for _f in new_values if _f])
        return source
