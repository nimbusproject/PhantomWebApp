username = casper.getPhantomUsername()
password = casper.getPhantomPassword()
phantom_url = casper.getPhantomURL()

casper.test.assertTruthy username, "PHANTOM_USERNAME is set"
casper.test.assertTruthy password, "PHANTOM_PASSWORD is set"

casper.echo "Phantom URL: #{phantom_url}"

casper.start phantom_url, ->
  @test.assertSelectorHasText "#nav-logout a", "Log In", "Make sure we're not logged in"
  @thenClick "#nav-logout a", ->
    @fill 'form[action="/accounts/login/"]',
      {"username": username, 'password': password}, true

casper.then ->
  @capture "log.png"
  @test.assertTitle "Phantom Home", "Login was successful"

casper.run ->
  @test.done 4
