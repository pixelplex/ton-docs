/**
 * @type {Array<{from: string, to: string}>}
 */


const redirects = [
  ...require('./redirects/common'),
  ...require('./redirects/learn'),
  ...require('./redirects/guidelines'),
  ...require('./redirects/documentation'),
];

module.exports = redirects;
