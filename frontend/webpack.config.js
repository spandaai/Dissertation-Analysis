const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');




module.exports = {
 entry: './src/index.js',  // Entry point to the app
 output: {
   path: path.resolve(__dirname, 'dist'),
   filename: 'bundle.js',  // Output file name
   clean: true,  // Clean the output directory before each build
 },
 mode: 'development',  // Can be changed to 'production' for production builds
 devServer: {
   static: path.join(__dirname, 'dist'),  // Serve files from 'dist' folder
   port: 4002,  // Dev server port
   open: true,  // Open browser automatically
   historyApiFallback: true,  // For React Router
 },
 module: {
   rules: [
     {
       test: /\.(js|jsx)$/,  // For JS and JSX files
       exclude: /node_modules/,
       use: {
         loader: 'babel-loader',  // Use Babel loader for JS/JSX
       },
     },
     {
       test: /\.css$/,  // For CSS files
       use: ['style-loader', 'css-loader'],
     },
     {
       test: /\.(png|jpe?g|gif|svg)$/i,  // For image files
       type: 'asset/resource',  // Use asset/resource to handle images
     },
     {
       test: /pdf\.worker\.js$/,
       use: { loader: 'worker-loader' }, // Use worker-loader for PDF.js worker
     },
   ],
 },
 plugins: [
   new HtmlWebpackPlugin({
     template: './public/index.html',  // HTML template for Webpack
   }),


 ],
 resolve: {
   extensions: ['.js', '.jsx'],  // Resolve JS and JSX files
   alias: {
     'pdfjs-dist/build/pdf.worker': 'pdfjs-dist/build/pdf.worker.entry',  // Alias for pdf worker
   },
 },
};
