import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon=True,
    install_requires=['cx_Oracle'],
)
