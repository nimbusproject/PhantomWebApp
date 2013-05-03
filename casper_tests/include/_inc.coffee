system = require('system')

casper.options.viewportSize = {width: 1000, height: 600}
casper.options.verbose = true
#casper.options.logLevel = 'debug'

casper.domain_name = "casper_test_domain"
casper.launch_config = "casper_test_lc"

casper.removeFilter = (filterName) ->
  if @_filters.hasOwnProperty filterName
    delete @_filters[filterName]


casper.getPhantomURL = ->
  phantomURL = system.env.PHANTOM_URL

  unless phantomURL
    phantomURL = "https://phantom.nimbusproject.org/"

  return phantomURL

casper.getPhantomUsername = ->
  username = system.env.PHANTOM_USERNAME

casper.getPhantomPassword = ->
  password = system.env.PHANTOM_PASSWORD

