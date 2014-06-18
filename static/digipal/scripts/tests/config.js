var config = {
    root: "http://localhost:80",
    tests: ['annotator', 'collections'],
    deepScan: false,
    scenarios: {
        path: "scenarios",
        excludes: []
    }
};

exports.config = config;