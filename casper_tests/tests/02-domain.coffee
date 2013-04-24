phantomURL = casper.getPhantomURL()

test_launch_config = "casper_domain_test_config"

casper.start phantomURL, ->
  @test.assertTitle "Phantom Home", "Make sure we're logged in"

casper.then ->
  @createLaunchConfig test_launch_config

casper.thenClick 'a[href="/phantom/domain"]', ->
  @t = Date.now()
  @test.info "Navigate to Domain page"

casper.then ->
  @test.info "Domain page load time: #{Date.now() - @t}ms"
  @test.assertTitle "Domains - Phantom",
      "Check that domain title is correct"
  @t = Date.now()

casper.waitFor (->
  return @evaluate ->
    return document.getElementById("phantom_domain_button_add")
      .hasAttribute("disabled") == false
  ),
  -> @test.info "Domains load time: #{Date.now() - @t}ms",
  -> @test.error "Page took too long to stop loading",
  10000



casper.thenClick '#phantom_domain_button_add', ->
  @test.info "Click Add Domain"

casper.waitUntilVisible '#phantom_domain_button_start', ->
  @evaluate ->
    document.getElementById('phantom_domain_size_input').value = 0

casper.thenClick '#phantom_domain_button_start', ->
  @test.info "Click Start"
  @t = Date.now()

casper.waitFor (->
  return @evaluate ->
    return document.getElementById("phantom_domain_button_add")
      .hasAttribute("disabled") == false
  ),
  -> @test.info "Domain start time: #{Date.now() - @t}ms",
  -> @test.error "Domain took too long to save",
  10000

casper.thenClick '#phantom_domain_button_terminate', ->
  @test.info "Click Terminate"
  @t = Date.now()

casper.waitFor (->
  return @evaluate ->
    return document.getElementById("phantom_domain_button_add")
      .hasAttribute("disabled") == false
  ),
  -> @test.info "Domain terminate time: #{Date.now() - @t}ms",
  -> @test.error "Domain took too long to terminate",
  10000

casper.then ->
  @capture "domain_screen.png"

casper.run ->
  @test.done()
