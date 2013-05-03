phantomURL = casper.getPhantomURL()

test_launch_config = "casper_domain_test_config"

casper.start phantomURL, ->
  @test.assertTitle "Phantom Home", "Make sure we're logged in"

casper.then ->
  @createLaunchConfig test_launch_config

casper.then ->
  n_domains = 5
  @test.info "Create #{n_domains} domains, then time loading them, then delete"

  domains = []
  domains.push "casper_test_domain#{i}" for i in [1..n_domains]

  @then @timeDomains

  @then ->
    @startDomain domainName for domainName in domains

  @then @timeDomains

  @then ->
    @terminateDomain domainName for domainName in domains

  @then @timeDomains

casper.then ->
  @capture "domain_screen.png"

casper.run ->
  @test.done()
