system = require('system')

casper.getPhantomURL = ->
  phantomURL = system.env.PHANTOM_URL

  unless phantomURL
    phantomURL = "https://phantom.nimbusproject.org/"

  return phantomURL

casper.getPhantomUsername = ->
  username = system.env.PHANTOM_USERNAME

casper.getPhantomPassword = ->
  password = system.env.PHANTOM_PASSWORD
