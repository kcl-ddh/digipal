# Digipal Tests

## Requirements
    - PhantomJS
    - CasperJS

## Usage
From command line, type:

    casperjs test digipal-test.js

Note that the parameter test is needed to make casperJS work in a test environment (and consequently to make asserts and tests work properly)

## Configuration (temporary)
Options to configure the tests:

    "root": "http://localhost:8000",
    "tests": ['titles', 'annotator'],
    "deepScan": false,
    "username": "gbuomprisco",
    "password": "DelPiero91"