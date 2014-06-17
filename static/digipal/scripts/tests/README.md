# Digipal Tests

## Requirements

    - PhantomJS
    - CasperJS

## Usage

From command line, type:

    casperjs test digipal-test.js

    Command line parameters:
    - --debug-remote: if true, also reports logs from the page being ran
    - --root: set your custom root
    - --username: username to access to protected pages
    - --password: password to access to protected pages
    - --deep: makes a full scan of the website (e.g. follows any link on the page, but same pages with different ids
        will be skipped ex. /digipal/page/61 and /digipal/page/34)

Note that the parameter test is needed to make casperJS work in a test environment (and consequently to make asserts and tests work properly)

## Configuration (temporary)

Options to configure the tests:

    -  root: website root
    -  tests: array of tests to be performed
    -  deepScan: deep scan of the website (all links will be followed by the script)

## Middleware and dependencies

It is possible to declare and include dependencies and middleware in a Scenario by specifing two variables inside the Scenario() function:

    function Scenario(){

        this.middleware = ['mymiddleware.js'] // this will be searched inside the folder middleware
        this.dependencies = ['./actions.js', ../anotherscenario/actions.js'] // this is relative to the current scenario

        // the middleware gets executed here ...

        this.Scenarios = function(dependencies, options){

            var actions = dependencies[0];
            var actions = dependencies[2];

            this.Scenario1 = function(){...};
            this.Scenario2 = function(){...};
            this.Scenario3 = function(){...};
        }
    }

The middleware functions work as a bridge between the scenario and the test suite. It can be useful for functions such as login, change of page, or for actions not related to the scenario to be performed prior to its initialization.

Dependencies get injected in a scenario through an array and are positionally declared.

## Strucutre

- Tests are performed in the file main.js. There you can choice which scenarios you want to run, and if repeat them for all the links or not.
- Scenarios are located in the folder scenarios. Every file in this folder will be scanned and ran as a scenario (even though, by convention it would be best the make one folder for scenario's type, and call the file scenario.js). Every scenario should need and action.js script, which should include actions to be ran in sequence inside scenarios. Actions can be shared among more scenarios and are exported as modules, as well as scenarios.