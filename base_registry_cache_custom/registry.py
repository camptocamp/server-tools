# Copyright 2025 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging
import typing

from odoo.modules import registry
from odoo.tools.lru import LRU
from odoo.tools.misc import OrderedSet

_logger = logging.getLogger(__name__)


def add_custom_cache(name: str, size: int, deps: typing.Iterable[str] = None):
    """Adds a custom cache into the Odoo registry

    :param name: name of the custom cache to add
    :param size: size of the custom cache (must be > 0)
    :param deps: iterable of other cache names, to be registered for cache
        invalidation dependencies; ``cache_name`` is always included as first item
    """
    _logger.info(f"Adding cache '{name}' to registries...")

    # ``registry._REGISTRY_CACHES`` is used by ``registry.Registry.init()`` to
    # initialize registries' caches (attr ``__cache``)
    registry._REGISTRY_CACHES[name] = size

    # ``registry._CACHES_BY_KEY`` is used by a variety of ``registry.Registry`` methods
    # to handle caches dependencies
    # NB: use an ``OrderedSet`` to avoid duplicates while keeping the dependency order
    # (with the main cache as first item anyway), then convert to tuple for consistency
    # w/ the standard ``registry._CACHES_BY_KEY`` structure
    registry._CACHES_BY_KEY[name] = tuple(OrderedSet([name] + list(deps or [])))

    # Update existing registries by:
    #   - adding the custom cache to the registry (name-mangle: avoid AttributeError)
    #   - setting up the proper signaling workflow
    # ``registry.Registry.registries`` is a class attribute that returns an
    # ``odoo.tools.lru.LRU`` object that maps each DB name to its ``registry.Registry``
    # object through its variable ``d`` (which is an ``OrderedDict`` object)
    for db_name, db_registry in registry.Registry.registries.d.items():
        _logger.info(f"Adding cache '{name}' to '{db_name}' registry")
        db_registry._Registry__caches[name] = LRU(size)
        db_registry.setup_signaling()
