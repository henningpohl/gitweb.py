from setuptools import setup

setup(
    name='gitweb.py',
    install_requires=[
        'web.py>=0.37',
        'pygments',
        'mako',
        'python-ldap',
        'GitPython'
    ]    
)


