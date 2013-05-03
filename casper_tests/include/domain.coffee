casper.ensureDomainPage = ->

  if @getCurrentUrl().search("domain") < 0
    @loadDomainPage()

casper.loadDomainPage = ->

  @thenClick 'a[href="/phantom/domain"]', ->
    @t = Date.now()
    @test.info "Navigate to Domain page"
    @capture 'domainstart.png'

  @then ->
    @test.assertUrlMatch /http.*\/domain$/,
        "Check that we are on domain page"

  @then ->
    @test.info "Domain page load time: #{Date.now() - @t}ms"
    @test.assertTitle "Domains - Phantom",
      "Check that domain title is correct"
    @t = Date.now()

  @waitFor (->
    return @evaluate ->
      return document.getElementById("phantom_domain_button_add")
        .hasAttribute("disabled") == false
    ),
    -> @test.info "Domains load time: #{Date.now() - @t}ms",
    -> @test.error "Page took too long to stop loading",
    10000

casper.timeDomains = ->

  @then ->
    @ensureDomainPage()

  @then ->
    @t = Date.now()
    @evaluate ->
      phantom_domain_load()

  @waitFor (->
    return @evaluate ->
      return document.getElementById("phantom_domain_button_add")
        .hasAttribute("disabled") == false &&
        document.getElementById("loading").style.display == "none"
    ),
    (-> @test.info "Domains load time: #{Date.now() - @t}ms"),
    (-> @test.error "Domains took too long to stop loading"),
    120000

casper.startDomain = (domainName) ->

  @then ->
    @then ->
      @ensureDomainPage()
      @t = Date.now()

    @waitFor (->
      return @evaluate ->
        return document.getElementById("phantom_domain_button_add")
          .hasAttribute("disabled") == false
      ),
      -> @test.info "Domain page load time: #{Date.now() - @t}ms",
      -> @test.error "Domain page took too long to terminate",
      10000


    @then ->
      @test.assertDoesntExist "#domain-#{domainName}",
        "#{domainName} doesn't already exist"
      @removeFilter 'page.prompt'

    @then ->
      @setFilter 'page.prompt', (msg, value) ->
        @test.info "Making domain #{domainName}"
        if msg == "Enter a new domain name:"
          return domainName

    @thenClick '#phantom_domain_button_add', ->
      @capture "clickstart.png"
      @t = Date.now()

    @waitForSelector "li.active #domain-#{domainName}",
      -> @test.info "Domain #{domainName} selected time : #{Date.now() - @t}ms",
      (->
        @test.error "domain was never selected"
        @capture "broken.png"
      ),
      10000

    @then ->
      @capture "active.png"
      @test.assertSelectorExists "li.active #domain-#{domainName}"

    @waitUntilVisible '#phantom_domain_start_buttons', (->
      @evaluate ->
        document.getElementById('phantom_domain_size_input').value = 0
      )
      , -> @test.info "Start button appear time: #{Date.now() - @t}ms"
      , -> @test.error "Took too long for start button to appear"
      , 10000

    @then ->
      @test.info "Selected domain: #{@fetchText '#phantom_domain_name_label'}"
      @capture "selected.png"
      @test.assertSelectorHasText "#phantom_domain_name_label", domainName

    @thenClick '#phantom_domain_button_start', ->
      @test.info "Click Start"
      @t = Date.now()

    @waitUntilVisible '#phantom_domain_running_buttons', (->
      @evaluate ->
        document.getElementById('phantom_domain_size_input').value = 0
      ),
      -> @test.info "Domain start time: #{Date.now() - @t}ms",
      -> @test.error "Domain took too long to save",
      10000

    @then ->
      @wait 5000 # This is a terrible hack while I try to figure out the bug
                 # in phantom while this is triggered
                 # something to do with the page reloading after starting
                 # a domain, while creating a new one
      @capture "create-domain-#{domainName}.png"

casper.terminateDomain = (domainName) ->

  @then ->
    @ensureDomainPage()
    @capture "terminate-domain-#{domainName}.png"
    @test.assertSelectorExists "a#domain-#{domainName}",
      "#{domainName} is available to terminate",

  @thenClick "a#domain-#{domainName}", ->
    @test.info "Terminating #{domainName}"

  @thenClick '#phantom_domain_button_terminate', ->
    @t = Date.now()

  @waitFor (->
    return @evaluate ->
      return document.getElementById("phantom_domain_button_add")
        .hasAttribute("disabled") == false
    ),
    -> @test.info "Domain terminate time: #{Date.now() - @t}ms",
    -> @test.error "Domain took too long to terminate",
    10000
