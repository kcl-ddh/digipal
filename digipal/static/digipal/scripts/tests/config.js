var config = {
    root: "http://localhost:80",
    tests: ['annotator', 'collections', 'titles'],
    deepScan: false,
    email_on_errors: false,
    scenarios: {
        path: "scenarios",
        excludes: []
    }
};

exports.config = config;