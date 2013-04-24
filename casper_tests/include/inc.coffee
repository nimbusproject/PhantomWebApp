system = require('system')

casper.options.viewportSize = {width: 1000, height: 600}
casper.options.verbose = true
#casper.options.logLevel = 'debug'

casper.domain_name = "casper_test_domain"
casper.launch_config = "casper_test_lc"

casper.removeFilter = (filterName) ->
  if @_filters.hasOwnProperty filterName
    delete @_filters[filterName]

casper.setFilter 'page.prompt', (msg, value) ->
  if msg == "Enter a new launch config name:"
    return casper.launch_config
  else if msg == "Enter a new domain name:"
    return casper.domain_name

casper.getPhantomURL = ->
  phantomURL = system.env.PHANTOM_URL

  unless phantomURL
    phantomURL = "https://phantom.nimbusproject.org/"

  return phantomURL

casper.getPhantomUsername = ->
  username = system.env.PHANTOM_USERNAME

casper.getPhantomPassword = ->
  password = system.env.PHANTOM_PASSWORD

