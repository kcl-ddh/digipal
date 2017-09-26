#
# PLEASE IGNORED THIS FILE
# TODO: bring it up to date and test
#
from pip.req import parse_requirements
from setuptools import setup, find_packages
import os
import digipal

install_reqs = parse_requirements('build/requirements.txt')

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Researchers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    "Programming Language :: Python :: 2.7",
]

setup(
    author="Peter Stokes",
    name='Archetype',
    version=digipal.__version__,
    description='Digital Resource and Database of Palaeography, Manuscript Studies and Diplomatic',
    long_description=open(os.path.join(
        os.path.dirname(__file__), 'README.md')).read(),
    url='https://archetype.ink',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=[str(ir.req) for ir in install_reqs],
    tests_require=[
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    # test_suite='runtests.main',
)
