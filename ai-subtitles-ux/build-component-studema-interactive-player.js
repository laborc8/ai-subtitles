const fs = require('fs-extra');
const concat = require('concat');
const package_json = require('./package.json');

console.log(package_json.version); // 1.2.4

build = async () => {
  const files = [
    './dist/studema-interactive-player/runtime.js',
    './dist/studema-interactive-player/polyfills.js',
    './dist/studema-interactive-player/main.js',
    //'./dist/studema-interactive-player/scripts.js',
    //'./dist/studema-interactive-player/vendor.js',
  ];

  await fs.ensureDir('widget');
  await concat(
    files,
    'widget/studema-widget-interactive-player-' + package_json.version + '.js'
  );
};
build();
