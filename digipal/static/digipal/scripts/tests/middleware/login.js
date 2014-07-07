var Middleware = function() {

    var Login = function(options, callback) {
        var username = casper.cli.get('username') || options.username;
        var password = casper.cli.get('password') || options.password;

        if (!username || !password) {
            casper.echo('This task needs username and password to the get root access', 'ERROR');
            casper.exit();
        }

        var AnnotatorActions = require('../scenarios/annotator/actions.js').Actions(options).actions;
        AnnotatorActions.get.adminAccess(options.root + '/admin', username, password, 132)
            .then(function() {
                return callback();
            });
    };
    return {
        'done': Login
    };
};

exports.Middleware = function() {
    return new Middleware();
};