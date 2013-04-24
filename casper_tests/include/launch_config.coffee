
# Launch config functions

casper.ensureLaunchConfigPage = ->

  if @getCurrentUrl().search("launchconfig") < 0
    @loadLaunchConfigPage()

casper.loadLaunchConfigPage = ->

  @thenClick 'a[href="/phantom/launchconfig"]', ->
    @t = Date.now()
    @test.info "Navigate to Launch Config page"
    @capture 'lcstart.png'

  @then ->
    @test.assertUrlMatch /http.*\/launchconfig$/,
        "Check that we are on Launch Config page"

  @waitFor (->
    return @evaluate ->
      return document.getElementById("phantom_lc_button_add")
        .hasAttribute("disabled") == false &&
        document.getElementById("loading").style.display == "none"
    ),
    ->
      @test.info "Launch Configs load time: #{Date.now() - @t}ms"
      @capture 'lc.png'
    ,
    ->
      @test.error "Launch Configs took too long to stop loading"
      @capture 'lc.png'
    , 10000


casper.timeLaunchConfigs = ->
  @then ->
    @t = Date.now()
    @evaluate ->
      phantom_lc_load()

  @waitFor (->
    return @evaluate ->
      return document.getElementById("phantom_lc_button_add")
        .hasAttribute("disabled") == false &&
        document.getElementById("loading").style.display == "none"
    ),
    (-> @test.info "Launch Configs load time: #{Date.now() - @t}ms"),
    (-> @test.error "Launch Configs took too long to stop loading"),
    120000


casper.createLaunchConfig = (launchConfigName, log = false) ->

  @then @ensureLaunchConfigPage

  @then ->
    @removeFilter 'page.prompt'
    @setFilter 'page.prompt', (msg, value) ->
      return launchConfigName

  @thenClick '#phantom_lc_button_add', ->
    if log then @test.info "Click Add Launch Config"

  @waitForSelector "#lc-#{launchConfigName}", ->
    @test.assertSelectorHasText "#launch_config_options_head",
      "#{launchConfigName} Launch Configuration",
      "#{launchConfigName} created"
    @test.assertSelectorExists '#cloud-row-sierra > .cloud-data-site',
      "Ensure Sierra is available"

  @thenClick '#cloud-row-sierra > .cloud-data-site', ->
    if log then @test.info "Choose Sierra, fill out form"
    @test.assertVisible '#cloud_options_name', "Cloud is selected"
    @evaluate ->
      document.getElementById('phantom_lc_max_vm').value = 1
      document.getElementById('phantom_lc_common_image_input').value =
        'hello-phantom.gz'

  @thenClick '#phantom_lc_add', ->
    if log then @test.info "Click Enable Site"
    @test.assertNotVisible '#phantom_lc_add',
      "Enable site button is hidden"
    @test.assertVisible '#phantom_lc_disable_cloud',
      "Disable site button is shown"

  @thenClick '#phantom_lc_save', ->
    if log then @test.info "Click Save"
    @t = Date.now()

  @waitFor (->
    return @evaluate ->
      return document.getElementById("phantom_lc_button_add")
        .hasAttribute("disabled") == false
    ),
    -> if log then @test.info "Launch config save time: #{Date.now() - @t}ms",
    -> @test.error "LC took too long to save",
    10000

casper.deleteLaunchConfig = (launchConfigName, log = false) ->

  @then @ensureLaunchConfigPage

  @then ->
    @test.assertSelectorExists "#lc-#{launchConfigName}",
      "#{launchConfigName} is available to Delete"

  @thenClick "#lc-#{launchConfigName}", ->
    if log then @test.info "Select #{launchConfigName} Launch Config"

  @then ->
    @test.assertSelectorHasText "#launch_config_options_head",
      "#{launchConfigName} Launch Configuration",
      "#{launchConfigName} is selected"
    @setFilter "page.confirm", (msg) ->
      return true

  @thenClick '#phantom_lc_delete', ->
    if log then @test.info "Click Delete #{launchConfigName}"
    @t = Date.now()

  @waitWhileSelector "#lc-#{launchConfigName}",
    -> if log then @test.info "Launch config delete time: #{Date.now() - @t}ms"
    -> @test.info "Launch config took too long to delete",
    10000


