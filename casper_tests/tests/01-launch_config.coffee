phantomURL = casper.getPhantomURL()

casper.start phantomURL, ->
  @test.assertTitle "Phantom Home", "Make sure we're logged in"

casper.then ->

  n_lcs = 5
  @test.info "Create #{n_lcs} LCs, then time loading them, then delete them"

  @ensureLaunchConfigPage()

  @then ->
    @timeLaunchConfigs()

  launch_configs = []
  launch_configs.push "casper_test_lc#{i}" for i in [1..n_lcs]
  @then ->
    @test.info "Creating launch configs #{launch_configs}"
    @createLaunchConfig lc for lc in launch_configs

  @then ->
    @test.info "Reloading launch configs"
    @timeLaunchConfigs()

  @then ->
    @test.assertSelectorExists("#lc-#{lc}") for lc in launch_configs

  @then ->
    @test.info "Deleting launch configs #{launch_configs}"
    @deleteLaunchConfig lc for lc in launch_configs

casper.then ->
  @capture "lc_screen.png"

casper.run ->
  @test.done()
