module.exports = function (grunt) {

    var appConfig = grunt.file.readJSON('package.json');

    const sass = require('node-sass')

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
            sass: this.app + '/static/sass',
            fonts: this.app + '/static/fonts',
            images: this.app + '/static/images',
            js: this.app + '/static/js',
            dist: this.app + '/static/dist',
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
		    implementation: sass,
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
		    implementation: sass,
                    outputStyle: 'nested',
                    sourceMap: false,
                    precision: 10
                },
                files: {
                    '<%= paths.dist %>/fontawesome.css': '<%= paths.bower %>/fontawesome/scss/font-awesome.scss',
                    '<%= paths.dist %>/common.css': '<%= paths.sass %>/common.scss',
                    '<%= paths.dist %>/search.css': '<%= paths.sass %>/search.scss',
                    '<%= paths.dist %>/grids.css': '<%= paths.sass %>/grids.scss',
                    '<%= paths.dist %>/bootstrap-fixes.css': '<%= paths.sass %>/bootstrap-fixes.scss',
                },
            },
            dist: {
                options: {
		    implementation: sass,
                    outputStyle: 'compressed',
                    sourceMap: false,
                    precision: 10
                },
                files: {
                    '<%= paths.dist %>/fontawesome.css': '<%= paths.bower %>/fontawesome/scss/font-awesome.scss',
                    '<%= paths.dist %>/common.css': '<%= paths.sass %>/common.scss',
                    '<%= paths.dist %>/search.css': '<%= paths.sass %>/search.scss',
                    '<%= paths.dist %>/grids.css': '<%= paths.sass %>/grids.scss',
                    '<%= paths.dist %>/bootstrap-fixes.css': '<%= paths.sass %>/bootstrap-fixes.scss',
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
                    "<%= paths.bower %>/js-cookie/src/js.cookie.js",
                    "<%= paths.js %>/search.js",
                    "<%= paths.js %>/grids.js",
                ],
                dest: "<%= paths.dist %>/project.js",
                nonull: true,
            },
            css: {
                src: [
                    "<%= paths.bower %>/bootstrap/dist/css/bootstrap.min.css",
                    "<%= paths.bower %>/tether/dist/css/tether.min.css",
                    "<%= paths.dist %>/fontawesome.css",
                    "<%= paths.dist %>/common.css",
                    "<%= paths.dist %>/contacts.css",
                    "<%= paths.dist %>/search.css",
                    "<%= paths.dist %>/content.css",
                    "<%= paths.dist %>/grids.css",
                    "<%= paths.dist %>/bootstrap-fixes.css",
                ],
                dest: "<%= paths.dist %>/project.css",
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
        },
    });

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
};
