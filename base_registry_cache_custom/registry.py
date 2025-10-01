# Copyright 2025 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging
import typing

from odoo.modules import registry
from odoo.tools.lru import LRU
from odoo.tools.misc import OrderedSet

from .exceptions import (
    CacheAlreadyExistsError,
    CacheInvalidConfigError,
    CacheInvalidDependencyError,
    CacheInvalidNameError,
)

_logger = logging.getLogger(__name__)


def add_custom_cache(
    name: str,
    count: int,
    depends_on_caches: typing.Iterable[str] = None,
    allows_direct_invalidation: bool = True,
    ignore_exceptions: typing.Iterable[type] = (),
):
    """Adds a custom cache into the Odoo registry

    :param name: name of the custom cache to add
    :param count: max capability of the custom cache; set as 1 if a lower value is given
    :param allows_direct_invalidation: if ``True``, a DB sequence is assigned to the
        cache is assigned any sequence and (therefore dotted names for such caches are
        not allowed) and method ``Registry.clear_cache()`` can be called directly for it
    :param depends_on_caches: iterable of other cache names: if set, the current cache
        will be listed as dependent on those caches, and invalidating one of them will
        invalidate the custom cache as well
    :param ignore_exceptions: iterable of Exception types: if set, no error is raised,
        but the cache is not added to the registries anyway
    """
    # Backup ``registry`` module attributes that needs restoring if something goes wrong
    registry_caches_backup = dict(registry._REGISTRY_CACHES)
    caches_by_key_backup = dict(registry._CACHES_BY_KEY)
    try:
        _add_custom_cache(name, count, depends_on_caches, allows_direct_invalidation)
    except Exception as exc:
        _logger.error(f"Could not add custom cache '{name}': {exc}")
        # Restore ``registry`` module attributes
        registry._REGISTRY_CACHES = registry_caches_backup
        registry._CACHES_BY_KEY = caches_by_key_backup
        # Raise error unless specified otherwise
        ignore_exceptions = tuple(ignore_exceptions or ())
        if not (ignore_exceptions and isinstance(exc, ignore_exceptions)):
            raise


def _add_custom_cache(
    name: str,
    count: int,
    depends_on_caches: typing.Iterable[str] = None,
    allows_direct_invalidation: bool = True,
):
    _logger.info(f"Adding cache '{name}' to registries...")

    # ``registry._REGISTRY_CACHES`` is used by ``registry.Registry.init()`` to
    # initialize registries' caches (attr ``__cache``)
    if name in registry._REGISTRY_CACHES:
        raise CacheAlreadyExistsError(f"Cache '{name}' already exists")
    normalized_count = max(count, 1)
    registry._REGISTRY_CACHES[name] = normalized_count

    # ``registry._CACHES_BY_KEY`` is used by a variety of ``registry.Registry``
    # methods to handle caches dependencies and DB signaling (main reason why a
    # cache that allows direct invalidation cannot have a dotted name)
    if allows_direct_invalidation:
        if "." in name:
            raise CacheInvalidNameError(f"Invalid cache name '{name}'")
        registry._CACHES_BY_KEY[name] = (name,)
    elif not depends_on_caches:
        raise CacheInvalidConfigError(
            f"Cache '{name}' should either allow direct invalidation"
            f" or depend on another cache for indirect invalidation"
        )

    # Setup invalidation dependencies recursively: if cache-3 depends on cache-2,
    # and cache-2 depends on cache-1, then invalidating cache-1 should invalidate
    # cache-3 too
    # NB: use an ``OrderedSet`` to avoid duplicates while keeping the dependency
    # order, then convert to tuple for consistency w/ the standard
    # ``registry._CACHES_BY_KEY`` structure
    if depends_on_caches:
        for cache in depends_on_caches or []:
            if cache not in registry._CACHES_BY_KEY:
                raise CacheInvalidDependencyError(
                    f"Cache '{name}' cannot depend on cache '{cache}':"
                    f" '{cache}' doesn't exist or doesn't allow direct invalidation"
                )
            deps = OrderedSet(registry._CACHES_BY_KEY[cache])
            registry._CACHES_BY_KEY[cache] = tuple(deps | {name})
        to_check = list(registry._CACHES_BY_KEY)
        while to_check:
            cache = to_check.pop(0)
            deps = OrderedSet(registry._CACHES_BY_KEY[cache])
            for dep in tuple(deps):
                for subdep in registry._CACHES_BY_KEY.get(dep) or []:
                    if subdep not in deps:
                        deps.add(subdep)
                        if cache not in to_check:
                            to_check.append(cache)
            registry._CACHES_BY_KEY[cache] = tuple(OrderedSet([cache]) | deps)

    # Update existing registries by:
    #   - adding the custom cache to the registry (name-mangle: no AttributeError)
    #   - setting up the proper signaling workflow
    # NB: ``registry.Registry.registries`` is a class attribute that returns an
    # ``odoo.tools.lru.LRU`` object that maps DB names to ``registry.Registry``
    # objects through variable ``d`` (which is a ``collections.OrderedDict`` object)
    for db_name, db_registry in registry.Registry.registries.d.items():
        _logger.info(f"Adding cache '{name}' to '{db_name}' registry")
        db_registry._Registry__caches[name] = LRU(normalized_count)
        if allows_direct_invalidation:
            db_registry.setup_signaling()
