If you need to create a custom cache, create a new module and:

- add this module as its dependency
- add a `post_load` hook like this:

```python
from odoo.addons.base_registry_cache_custom.registry import add_custom_cache


def post_load():
    add_custom_cache(name="my_cache", size=256)
```

If you make use of multiple caches, and some of them should be invalidated when another
one gets invalidated itself, use the `deps` argument:

```python
from odoo.addons.base_registry_cache_custom.registry import add_custom_cache


def post_load():
    add_custom_cache(name="my_cache", size=256, deps=["my_cache.subcache"])
    add_custom_cache(name="my_cache.subcache", size=128)
```
