phantomURL = casper.getPhantomURL()

casper.start phantomURL, ->
  @test.assertTitle "Phantom Home", "Make sure we're logged in"

casper.thenClick 'a[href="/phantom/launchconfig"]', ->
  @t = Date.now()

casper.then ->
  @test.info "Launch Config took #{Date.now() - @t}ms to load"
  @test.assertTitle "Launch Configurations - Phantom",
      "Check that lc title is correct"

casper.run ->
  @test.done 2
