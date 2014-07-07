from setuptools import setup, find_packages
import os
import digipal

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
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
]

setup(
    author="Peter Stokes",
    name='digipal',
    version=digipal.__version__,
    description='Digital Resource and Database of Palaeography, Manuscript Studies and Diplomatic',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    url='http://www.digipal.eu/',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=[
        'Django>=1.6',
        'Mezzanine==3.1.5',
        'South',
        'Whoosh>=2.6.0',
        'disqus-python',
        'git+git://github.com/toastdriven/django-haystack.git@1274a8d1bc5b34348a6dd9405284b91b1e246747#egg=django_haystack-dev',
        'git+git://github.com/geoffroy-noel-ddh/django-iipimage@0.1.0',
        'git+git://github.com/Gbuomprisco/django-pagination.git@a4f31508609aa39063dfa087c26aade471f1480e#egg=django_pagination-dev',
        'django-reversion>=1.8.1',
        'django-tinymce',
        #'future',
        #'lxml',
        # For postgreSQL database
        #'psycopg2',
        #'PIL',
        #'pillow',
        'pyelasticsearch==0.6.1',
    ],
    tests_require=[
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    #test_suite='runtests.main',
)

