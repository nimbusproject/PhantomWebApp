phantomURL = casper.getPhantomURL()

casper.start phantomURL, ->
  @test.assertTitle "Phantom Home", "Make sure we're logged in"

casper.thenClick 'a[href="/phantom/profile"]', ->
  @t = Date.now()

casper.then ->
  @test.info "Profile took #{Date.now() - @t}ms to load"
  @test.assertTitle "Profile - Phantom", "Check that profile title is correct"

casper.run ->
  @test.done 2
