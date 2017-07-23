const path = require('path');
const webpack = require('webpack');

 module.exports = {
     entry: path.resolve(__dirname, 'socialhome/client/app.js'),
     output: {
         path: path.resolve(__dirname, 'socialhome/static/js'),
         filename: 'webpack.bundle.js'
     },
     module: {
         loaders: [
             {
                 test: /.js$/,
                 loader: 'babel-loader',
                 query: {
                     presets: ['es2017']
                 }
             }
         ]
     },
     stats: {
         colors: true
     },
     devtool: 'source-map'
 };
