module.exports = function (grunt) {

    var appConfig = grunt.file.readJSON('package.json');

    // Load grunt tasks automatically
    // see: https://github.com/sindresorhus/load-grunt-tasks
    require('load-grunt-tasks')(grunt);

    // Time how long tasks take. Can help when optimizing build times
    // see: https://npmjs.org/package/time-grunt
    require('time-grunt')(grunt);

    var pathsConfig = function (appName) {
        this.app = appName || appConfig.name;

        return {
            app: this.app,
            templates: this.app + '/templates',
            css: this.app + '/static/css',
            sass: this.app + '/static/sass',
            fonts: this.app + '/static/fonts',
            images: this.app + '/static/images',
            js: this.app + '/static/js',
            mocha: this.app + '/static/mocha',
            manageScript: 'manage.py',
            bower: "bower_components",
            node: "node_modules",
        }
    };

    grunt.initConfig({

        paths: pathsConfig(),
        pkg: appConfig,

        // see: https://github.com/gruntjs/grunt-contrib-watch
        watch: {
            gruntfile: {
                files: ['Gruntfile.js']
            },
            sass: {
                files: [
                    '<%= paths.sass %>/**/*.{scss,sass}',
                    '<%= paths.js %>/**/*.js',
                ],
                tasks: ['sass:dev', 'concat', 'copy'],
                options: {
                    atBegin: true
                }
            },
            livereload: {
                files: [
                    '<%= paths.js %>/**/*.js',
                    '<%= paths.sass %>/**/*.{scss,sass}',
                    '<%= paths.app %>/**/*.html'
                ],
                options: {
                    spawn: false,
                    livereload: true,
                },
            },
        },

        // see: https://github.com/sindresorhus/grunt-sass
        sass: {
            dev: {
                options: {
                    outputStyle: 'nested',
                    sourceMap: false,
                    precision: 10
                },
                files: {
                    '<%= paths.css %>/fontawesome.css': '<%= paths.bower %>/fontawesome/scss/font-awesome.scss',
                    '<%= paths.css %>/common.css': '<%= paths.sass %>/common.scss',
                    '<%= paths.css %>/grids.css': '<%= paths.sass %>/grids.scss',
                    '<%= paths.css %>/streams.css': '<%= paths.sass %>/streams.scss',
                    '<%= paths.css %>/publisher.css': '<%= paths.sass %>/publisher.scss',
                    '<%= paths.css %>/content.css': '<%= paths.sass %>/content.scss',
                },
            },
            dist: {
                options: {
                    outputStyle: 'compressed',
                    sourceMap: false,
                    precision: 10
                },
                files: {
                    '<%= paths.css %>/fontawesome.css': '<%= paths.bower %>/fontawesome/scss/font-awesome.scss',
                    '<%= paths.css %>/common.css': '<%= paths.sass %>/common.scss',
                    '<%= paths.css %>/grids.css': '<%= paths.sass %>/grids.scss',
                    '<%= paths.css %>/streams.css': '<%= paths.sass %>/streams.scss',
                    '<%= paths.css %>/publisher.css': '<%= paths.sass %>/publisher.scss',
                    '<%= paths.css %>/content.css': '<%= paths.sass %>/content.scss',
                },
            }
        },

        concat: {
            js: {
                src: [
                    "<%= paths.bower %>/jquery/dist/jquery.min.js",
                    "<%= paths.bower %>/tether/dist/js/tether.min.js",
                    "<%= paths.bower %>/jquery-ui/jquery-ui.min.js",
                    "<%= paths.bower %>/underscore/underscore-min.js",
                    "<%= paths.bower %>/bootstrap/dist/js/bootstrap.min.js",
                    "<%= paths.bower %>/masonry/dist/masonry.pkgd.min.js",
                    "<%= paths.bower %>/imagesloaded/imagesloaded.pkgd.min.js",
                    "<%= paths.bower %>/reconnecting-websocket/reconnecting-websocket.min.js",
                    "<%= paths.bower %>/bootstrap-markdown/js/bootstrap-markdown.js",
                    "<%= paths.bower %>/js-cookie/src/js.cookie.js",
                    "<%= paths.js %>/vendor/appear.min.js",
                    "<%= paths.js %>/content.js",
                    "<%= paths.js %>/grids.js",
                    "<%= paths.js %>/streams.js",
                    "<%= paths.js %>/publisher.js",
                ],
                dest: "<%= paths.js %>/project.js",
                nonull: true,
            },
            css: {
                src: [
                    "<%= paths.bower %>/bootstrap/dist/css/bootstrap.min.css",
                    "<%= paths.bower %>/tether/dist/css/tether.min.css",
                    "<%= paths.bower %>/bootstrap-markdown/css/bootstrap-markdown.min.css",
                    "<%= paths.css %>/fontawesome.css",
                    "<%= paths.css %>/common.css",
                    "<%= paths.css %>/grids.css",
                    "<%= paths.css %>/streams.css",
                    "<%= paths.css %>/publisher.css",
                    "<%= paths.css %>/content.css",
                ],
                dest: "<%= paths.css %>/project.css",
                nonull: true,
            },
        },

        //see https://github.com/nDmitry/grunt-postcss
        postcss: {
            options: {
                map: true, // inline sourcemaps
                processors: [
                    require('pixrem')(), // add fallbacks for rem units
                    require('autoprefixer-core')({
                        browsers: [
                            'Android 2.3',
                            'Android >= 4',
                            'Chrome >= 20',
                            'Firefox >= 24',
                            'Explorer >= 8',
                            'iOS >= 6',
                            'Opera >= 12',
                            'Safari >= 6'
                        ]
                    }), // add vendor prefixes
                    require('cssnano')() // minify the result
                ]
            },
            dist: {
                src: '<%= paths.css %>/*.css'
            }
        },

        copy: {
            font_awesome: {
                expand: true,
                flatten: true,
                src: ['<%= paths.bower %>/fontawesome/fonts/*'],
                dest: '<%= paths.fonts %>'
            },
            mocha: {
                expand: true,
                flatten: true,
                src: [
                    "<%= paths.node %>/mocha/mocha.js",
                    "<%= paths.node %>/mocha/mocha.css",
                    "<%= paths.node %>/chai/chai.js",
                    "<%= paths.bower %>/mock-socket/dist/mock-socket.js",
                ],
                dest: "<%= paths.mocha %>/",
            },
            sinon: {
                src: "<%= paths.bower %>/sinon/index.js",
                dest: "<%= paths.mocha %>/sinon.js",
            },
        },

        // see: https://npmjs.org/package/grunt-bg-shell
        bgShell: {
            _defaults: {
                bg: true,
            },
            runDjango: {
                cmd: 'python <%= paths.manageScript %> runserver',
            },
            runDjangoTest: {
                cmd: 'MOCHA_RUNSERVER_PORT=8181 python <%= paths.manageScript %> runserver 8181',
            },
            killDjangoTest: {
                cmd: 'kill `pgrep -f "runserver 8181"`',
            },
            sleep: {
                cmd: 'sleep 5',
                bg: false,
            },
        },
        mocha: {
            'socialhome.streams': {
                options: {
                    urls: ['http://127.0.0.1:8181/mocha/streams/'],
                    run: true,
                    logErrors: true,
                    log: true,
                    reporter: "nyan",
                }
            },
            'socialhome.content': {
                options: {
                    urls: ['http://127.0.0.1:8181/mocha/content/'],
                    run: true,
                    logErrors: true,
                    log: true,
                    reporter: "nyan",
                }
            },
        },
    });

    // Tip from http://stackoverflow.com/a/19673597/1489738
    var previous_force_state = grunt.option("force");
    grunt.registerTask("force", function(set) {
        if (set === "on") {
            grunt.option("force", true);
        }
        else if (set === "off") {
            grunt.option("force", false);
        }
        else if (set === "restore") {
            grunt.option("force", previous_force_state);
        }
    });

    grunt.registerTask('test', [
        'bgShell:runDjangoTest',
        'bgShell:sleep',
        'force:on',
        'mocha',
        'force:off',
        'bgShell:killDjangoTest',
    ]);

    grunt.registerTask('serve', [
        'bgShell:runDjango',
        'watch'
    ]);

    grunt.registerTask('build', [
        'sass:dist',
        'postcss',
        'concat',
        'copy',
    ]);

    grunt.registerTask('dev', [
        'sass:dev',
        'concat',
        'copy',
    ]);

    grunt.registerTask('default', [
        'dev'
    ]);

    grunt.loadNpmTasks('grunt-mocha');
};
