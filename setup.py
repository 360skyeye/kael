"""
kael
"""
import re
import ast
from setuptools import setup, find_packages

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('kael/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='kael',
    version=version,
    url='https://github.com/360skyeye',
    license='Apache-2.0',
    author='360skyeye',
    author_email='liqiongxiang@b.360.cn',
    description='A micro service framework based on MQ',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'gevent>=1.1.2',
        'msgpack-python>=0.4.8',
        'pika>=0.10.0',
        'PyYAML>=3.12',
        'termcolor>=1.1.0',
        'beautifultable',
        'click>=4.0',
        'python-crontab>=2.2.2',
        'simplejson',
        'pymongo',
        'flask_redis',
        'jsonschema',
        'flask'
    ],
    extras_require={},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points={
        'console_scripts': [
            'kael=kael.cli:main',
            'kael-crontab=kael.cron:kael_crontab',
            'kael-web=kael.web_cli:web_main',
        ]
        
    }
)
