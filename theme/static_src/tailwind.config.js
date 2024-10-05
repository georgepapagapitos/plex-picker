module.exports = {
    content: [
      '../../templates/**/*.html',
      '../../**/templates/**/*.html',
      '../../static/js/**/*.js',
    ],
    theme: {
      extend: {},
    },
    plugins: [
      require('@tailwindcss/forms'),
      require('@tailwindcss/typography'),
      require('@tailwindcss/aspect-ratio'),
    ],
  }