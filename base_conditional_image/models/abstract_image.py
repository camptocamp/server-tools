# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval


class AbstractConditionalImage(models.AbstractModel):
    _name = "abstract.conditional.image"
    _description = "Abstract image"
    _inherit = "image.mixin"

    image_1920 = fields.Image(compute="_compute_images", store=False, readonly=True)
    image_1024 = fields.Image(compute="_compute_images", store=False, readonly=True)
    image_512 = fields.Image(compute="_compute_images", store=False, readonly=True)
    image_256 = fields.Image(compute="_compute_images", store=False, readonly=True)
    image_128 = fields.Image(compute="_compute_images", store=False, readonly=True)

    @staticmethod
    def _compute_selector_test_without_company(image_selector, record):
        return bool(safe_eval(image_selector.selector or "True", {"object": record}))

    @staticmethod
    def _compute_selector_test_with_company(image_selector, record):
        if (
            image_selector.company_id == record.company_id
            or record.company_id
            and not image_selector.company_id
        ):
            return AbstractConditionalImage._compute_selector_test_without_company(
                image_selector, record
            )
        return False

    def _compute_images(self):
        if "company_id" in self._fields:
            search_clause = [("model_name", "=", self._name)]
            test_method = self._compute_selector_test_with_company
        else:
            # If inherited object doesn't have a `company_id` field,
            # remove the items with a company defined and the related checks
            search_clause = [
                ("model_name", "=", self._name),
                ("company_id", "=", False),
            ]
            test_method = self._compute_selector_test_without_company

        image_selectors = self.env["image"].search(
            search_clause, order="company_id, selector"
        )

        for rec in self:
            found = None
            for image_selector in image_selectors:
                if test_method(image_selector, rec):
                    found = image_selector
                    break
            if found:
                rec.update(
                    {
                        "image_1920": found.image_1920,
                        "image_1024": found.image_1024,
                        "image_512": found.image_512,
                        "image_256": found.image_256,
                        "image_128": found.image_128,
                    }
                )
