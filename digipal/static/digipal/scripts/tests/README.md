# Digipal Tests

## Requirements

    - PhantomJS
    - CasperJS

## Usage

From command line, type:

    casperjs test main.js

    Command line parameters:
    - --debug-remote: if true, also reports logs from the page being ran
    - --root: set your custom root
    - --username: username to access to protected pages
    - --password: password to access to protected pages
    - --deep: makes a full scan of the website (e.g. follows any link on the page, but same pages with different ids
        will be skipped ex. /digipal/page/61 and /digipal/page/34)
    - --exclude-test: list of test names separated by comma to be excluded ex. --exclude-test=annotator,titles

Note that the parameter test is needed to make casperJS work in a test environment (and consequently to make asserts and tests work properly)

## Configuration (temporary)

Options to configure the tests:

    -  root: website root
    -  tests: array of tests to be performed
    -  deepScan: deep scan of the website (all links will be followed by the script)

## Main file

The main file is used to istantiate the tests and configure the tests to be executed.
A simple snippet to run the script:

    phantom.page.injectJs('./test-suite.js');
    var Tester = new TestSuite();

    var Test1 = {
        multiple: false,
        name: 'test1',
        run: function(loadScenarios) {
            var scenarios = ['myscenario', 'myscenario2'];
            loadScenarios(scenarios);
        }
    };

    Tester.addTest(Test1);
    Tester.init();

The function Tester.addTest accepts an undetermined number of tests to be executed. So we can have:

    Tester.addTest(Test1, Test2, Test3);

It is very important to be careful about the name of a test, because it must match with the list of tests we provide in the config.js file.

## Scenarios, Middleware and dependencies

Dependencies and middleware get injected in a scenario through an object used inside the list of Scenarios. This is a quick example of how to define and initialize it.

A function Scenario has two properties:

- dependencies: an array with the paths to the dependencies we want
- middleware: an array with the paths to the middlewares we want

Middleware will be arbitrarly executed before running the scenarios, the dependencies will be injected through the function Scenarios, so that they will be ready to be used in Scenarios.

### Define a Scenario

It is possible to declare and include dependencies and middleware in a Scenario by specifing two variables inside the Scenario() function:

    var Scenario = function(){

        this.middleware = ['middleware.js'] // this will be searched inside the folder middleware
        this.dependencies = ['./actions.js', ../anotherscenario/actions.js'] // this is relative to the current scenario

        // the middleware gets executed here ...

        this.Scenarios = function(dependencies, options){

            // the dependencies are encapsulated into the object dependencies

            var actions = dependencies.nameDependency;
            var actions2 = dependencies.nameDependency2;

            this.Scenario1 = function(){...};
            this.Scenario2 = function(){...};
            this.Scenario3 = function(){...};
        }
    }

    exports.Scenario = new Scenario();

### Define a dependency module

    var Actions = function(options){

        this.name = 'myDependencyModule';

        this actions = {
            // my actions
        };

    }

    exports.Actions = function(options){
        return new Actions(options);
    };


### Define a middleware

    var Middleware = function(options, callback) {

       function myFunction(options, callback){
        // do something
       };

        // remember to always return the done function

        return {
            'done': myFunction
        };
    };

    exports.Middleware = function() {
        return new Middleware();
    };

The middleware functions work as a bridge between the scenario and the test suite. It can be useful for functions such as login, change of page, or for actions not related to the scenario to be performed prior to its initialization. The callback function makes sure that the middleware has been done before running the scenarios.
