var g_cloud_map = {};
var g_selected_cloud = null;
var ENTER_KEYCODE = 13;
var g_chef_servers = {};
var g_selected_chef = null;

function jq(myid) {
    return '#' + myid.replace(/(:|\.)/g,'\\$1');
}

$(document).ready(function() {
    $("#nav-profile").addClass("active");
    $('a.nav-profile-menu').click(function (e) {
        e.preventDefault();
        window.location.hash = $(this).attr("href");
        $(this).tab('show');
        return false;
    });

    $("#phantom_cloud_edit_add").click(function() {
        phantom_cloud_edit_add_click();
        return false;
    });

    $("#phantom_cloud_edit_remove").click(function() {
        phantom_cloud_edit_remove_click();
        return false;
    });

    $("#phantom_cloud_edit_name").change(function() {
        phantom_cloud_edit_change_cloud();
        return false;
    });

    $("#cloud_table_body").on('click', 'tr', function(event){
        $(this).parent().children().removeClass("info");
        var cloud_name = $(this).children().first().text();
        phantom_cloud_edit_change_cloud(cloud_name);
        return false;
    });


    $("#change_password_button").click(function() {
        change_password_click();
        return false;
    });

    $("#add-chef-server").click(function() {
        add_chef_server($("#chef-credentials-name").val());
        $("#add-chef-modal").modal('hide');
        return false;
    });

    $("#add-chef-form").submit(function() {
        add_chef_server($("#chef-credentials-name").val());
        $("#add-chef-modal").modal('hide');
        return false;
    });

    $("#add-chef-modal").on('show', function() {
        $("#chef-credentials-name").val("");
    });

    $("#add-chef-modal").on('shown', function() {
        $("#chef-credentials-name").focus();
    });

    $("#chef-nav").on('click', "a.chef-server", function() {
        var chef_server_id = $(this).attr("id");
        var chef_server_name = chef_server_id.split("chef-server-")[1];
        select_chef_server(chef_server_name);
        return false;
    });

    $("#chef-save").click(function() {
        save_chef_server();
        return false;
    });

    $("#chef-remove").click(function() {

        remove_chef_server();
        return false;
    });

    $(document).keypress(function(e) {
        if (e.which == ENTER_KEYCODE) {

            if ($("#account-settings").is(":visible")) {
                change_password_click();
            }
        }
    });

    if (window.location.hash === "#account-settings") {
        window.scrollTo(0, 0);
        $("#domain-nav a[href=#account-settings]").tab("show");
    }
    else if (window.location.hash === "#chef-credentials") {
        window.scrollTo(0, 0);
        $("#domain-nav a[href=#chef-credentials]").tab("show");
    }
    else { // Default
        window.scrollTo(0, 0);
        $("#domain-nav a[href=#cloud-credentials]").tab("show");
        $("#").addClass("active");
    }

    phantom_cloud_edit_load_page();
    load_chef_servers();
});

function add_chef_server(chef_server_name) {

    if (!chef_server_name) {
        return false;
    }

    var new_chef_server = "<li><a href='#' class='chef-server' id='chef-server-" +
        chef_server_name + "'>" + chef_server_name + "</a></li>";
    $("#chef-header").after(new_chef_server);
    g_chef_servers[chef_server_name] = {};
    select_chef_server(chef_server_name);
}

function select_chef_server(chef_server_name) {

    if (!chef_server_name) {
        return false;
    }

    if (!chef_server_name in g_chef_servers) {
        return false;
    }

    $("#chef-server-form").show();

    $("a.chef-server").parent().removeClass("active");
    $("a#chef-server-" + chef_server_name).parent().addClass("active");

    var chef_server = g_chef_servers[chef_server_name];

    $("#chef-url").val(chef_server['server_url']);
    $("#chef-client-name").val(chef_server['client_name']);
    $("#chef-validator-name").val(chef_server['validation_client_name']);
    $("#chef-client-key").val(chef_server['client_key']);
    $("#chef-validator-key").val(chef_server['validator_key']);

    g_selected_chef = chef_server_name;
}

function save_chef_server() {

    if (!g_selected_chef) {
        return false;
    }

    var update = false;
    if ((g_selected_chef in g_chef_servers) && !$.isEmptyObject(g_chef_servers[g_selected_chef])) {
        update = true;
    }

    var credentials = {
        'id': g_selected_chef,
        'server_url': $("#chef-url").val(),
        'validation_client_name': $("#chef-validator-name").val(),
        'client_name': $("#chef-client-name").val(),
        'client_key': $("#chef-client-key").val(),
        'validator_key': $("#chef-validator-key").val(),
    };

    var success_func = function(ret) {
        g_chef_servers[g_selected_chef] = credentials;
        phantom_cloud_edit_enable(true);
    }

    var error_func = function(err) {
        phantom_alert("Problem saving Chef Credentials: " + err);
        phantom_cloud_edit_enable(true);
    }

    if (update) {
        var url = make_url("credentials/chef/" + g_selected_chef);
        phantomPUT(url, credentials, success_func, error_func);
    }
    else {
        var url = make_url("credentials/chef");
        phantomPOST(url, credentials, success_func, error_func);
    }
    phantom_info("Saving chef credentials...");
    phantom_cloud_edit_enable(false);
}

function remove_chef_server() {

    if (!g_selected_chef) {
        return false;
    }

    var success_func = function (obj) {
        load_chef_servers();
    }

    var error_func = function(obj, message) {
        phantom_alert(message);
        phantom_cloud_edit_enable(true);
    }

    var url = make_url("credentials/chef/" + g_selected_chef);
    phantom_cloud_edit_enable(false);
    phantomDELETE(url, success_func, error_func);
}

function load_chef_servers() {

    function loaded(chef_credentials) {

        var chef_servers = {};
        for (var i=0; i<chef_credentials.length; i++) {
            var credential = chef_credentials[i];
            chef_servers[credential['id']] = credential;
        }

        g_chef_servers = chef_servers;

        var first_chef_server = null;
        for (var chef_server_name in g_chef_servers) {
            if (first_chef_server === null) {
                first_chef_server = chef_server_name;
            }
            var new_chef_server = "<li><a href='#' class='chef-server' id='chef-server-" +
                chef_server_name + "'>" + chef_server_name + "</a></li>";
            $("#chef-header").after(new_chef_server);
        }

        select_chef_server(first_chef_server);
    }

    var error_func = function(obj, message) {
        phantom_alert(message);
        phantom_cloud_edit_enable(true);
    }

    var url = make_url('credentials/chef');
    phantomGET(url, loaded, error_func);
}

function phantom_cloud_edit_enable(enable) {
    if(enable) {
        $("input, textarea, select").removeAttr("disabled", "disabled");

        if ($("#phantom_cloud_edit_keyname_list").children().length === 0) {
            $("#phantom_cloud_edit_keyname_list").parent().parent().hide();
        }
        else {
            $("#phantom_cloud_edit_keyname_list").parent().parent().show();
        }

        $('#loading').hide();
        $('#alert-container').empty();
    }
    else {
        $("input, textarea, select").attr("disabled", "disabled");
        $('#loading').show();
    }
}

function change_password_click() {
 
    $("#password-form .help-inline").remove();
    $("#password-form div").removeClass("error").removeClass("success");

    var old_password = $("#old_password").val();
    var new_password = $("#new_password").val();
    var new_password_confirm = $("#new_password_confirmation").val();

    var params = {
        "old_password": old_password,
        "new_password": new_password,
        "new_password_confirmation": new_password_confirm,
    };

    var success_func = function(obj) {
        $("#change_password_button")
            .after('<span class="help-inline"><i class="icon-ok"></i> Password Changed</span>')
            .removeAttr("disabled")
            .parent().parent().addClass("success");
    };

    var error_func = function(url, error_message) {
        $("#change_password_button").removeAttr("disabled");
        if (error_message === "BAD_OLD_PASSWORD") {
            $("#old_password").after('<span class="help-inline">Incorrect password</span>')
                .parent().parent().addClass("error");

        }
        else if (error_message === "PASSWORDS_DO_NOT_MATCH") {
            $("#new_password").parent().parent().addClass("error");
            $("#new_password_confirmation").after('<span class="help-inline">Passwords do not match</span>')
                .parent().parent().addClass("error");
        }
        else {
            phantom_alert("UNKNOWN ERROR: " + error_message);
        }
    };

    $("#change_password_button").attr("disabled", true);
    var url = '/accounts/ajax_change_password/';
    phantomPOST(url, params, success_func, error_func);
}

function phantom_cloud_edit_add_click() {

    $("#cloud-credentials .help-inline").remove();
    $("#cloud-credentials div").removeClass("error");

    var nameCtl = $("#cloud_table_body tr.info td").first().text();
    //var nameCtl = $("#phantom_cloud_edit_name").val().trim();
    var accessCtl = $("#phantom_cloud_edit_access").val().trim();
    var secretCtl = $("#phantom_cloud_edit_secret").val().trim();
    var keyCtl = $("#phantom_cloud_edit_keyname_list").val();

    var error_msg = undefined;
    if(! nameCtl) {
        error_msg = "You must name your cloud."
    }
    if(! accessCtl) {
        $("#phantom_cloud_edit_access")
            .after('<span class="help-inline">You must set an access key</span>')
            .parent().parent().addClass("error");
        return;
    }
    if(! secretCtl) {
        $("#phantom_cloud_edit_secret")
            .after('<span class="help-inline">You must set a secret key</span>')
            .parent().parent().addClass("error");
        return;
    }
    if(keyCtl == undefined) {
        keyCtl = "";
    }

    if (error_msg) {
        phantom_alert(error_msg);
        return;
    }

    //send call to service
    var success_func = function (obj) {
        phantom_cloud_edit_load_sites();
    }

    var error_func = function(obj, message) {
        phantom_alert(message);
        phantom_cloud_edit_enable(true);
    }

    var url = make_url('credentials/sites');
    phantom_cloud_edit_enable(false);
    phantomPOST(url, {'id': nameCtl, 'access_key': accessCtl, 'secret_key': secretCtl, 'key_name': keyCtl}, success_func, error_func);
}


function phantom_cloud_edit_change_cloud_internal(selected_cloud_name)  {

    if (!selected_cloud_name) {
        if (g_selected_cloud) {
            selected_cloud_name = g_selected_cloud;
        }
        else {
            selected_cloud_name = $("#cloud_table_body tr td").first().text();
        }
    }

    g_selected_cloud = selected_cloud_name;

    $(".control-group").removeClass("error");

    $(jq("cloud-row-" + selected_cloud_name)).addClass("info");

    var credentials = g_cloud_map[selected_cloud_name];

    $("#phantom_cloud_edit_key_message").text("");
    $("#phantom_cloud_edit_keyname_list").empty();
    if (!credentials || !credentials['access_key'] || !credentials['secret_key']) {
        $("#phantom_cloud_edit_access").val("");
        $("#phantom_cloud_edit_secret").val("");
        $("#phantom_cloud_edit_keyname_list").parent().parent().hide();
    }
    else {
        $("#phantom_cloud_edit_keyname_list").parent().parent().show();
        $("#phantom_cloud_edit_access").val(credentials['access_key']);
        $("#phantom_cloud_edit_secret").val(credentials['secret_key']);
        if (credentials.status_msg) {
            phantom_alert(val.status_msg);
        }
        for (keyndx in credentials.keyname_list) {
            $("#phantom_cloud_edit_key_message").val("");
            key = credentials.keyname_list[keyndx]
            var new_choice = $('<option>',  {'name': key, value: key, text: key});
            $("#phantom_cloud_edit_keyname_list").append(new_choice);
        }
        if(credentials.key_name == undefined || credentials.key_name == "") {
            var msg = "Please set an ssh key and save.";
            $("#phantom_cloud_edit_keyname_list").parent().children(".help-inline").remove();
            $("#phantom_cloud_edit_keyname_list")
                .after('<span class="help-inline">' + msg + '</span>')
                .parent().parent().addClass("error");
        }
        else {
            $("#phantom_cloud_edit_keyname_list").val(credentials.key_name);
        }

    }
}

function show_cloud_edit_guides() {
        $("#phantom_cloud_edit_access")
            .after('<span class="help-inline">Password Changed</span>');
    
}

function phantom_cloud_edit_change_cloud (cloud_name) {
    try {
        phantom_cloud_edit_change_cloud_internal(cloud_name);
    }
    catch(err) {
        phantom_alert(err);
    }
}

function make_cloud_table_row(site, status) {

    if (status === "Enabled") {
        status = '<span class="label label-success">' + status + '</span>';
    }
    else if (status === "Incomplete") {
        status = '<span class="label label-warning">' + status + '</span>';
    }
    else if (status === "Disabled") {
        status = '<span class="label">' + status + '</span>';
    }
    else {
        status = '<span class="label">' + status + '</span>';
    }

    var row = "<tr id='cloud-row-" + site + "'>" +
      "<td class='cloud-data-site'>" + site + "</td>" +
      "<td>" + status + "</td>" +
      "</tr>";
    return row;
}

function phantom_cloud_edit_load_sites() {

    var credentials_loaded = function(credentials){

        $("#cloud-credentials .help-inline").remove();
        $("#cloud_table_body").empty();
        var selected_cloud_name = $("#phantom_cloud_edit_name").val();

        var credentials_map = {};

        for (var i = 0; i < credentials.length; i++) {
            var credential = credentials[i];
            if (credential.hasOwnProperty("id")) {

                g_cloud_map[credential.id]["key_name"] = credential["key_name"];
                g_cloud_map[credential.id]["access_key"] = credential["access_key"];
                g_cloud_map[credential.id]["secret_key"] = credential["secret_key"];
                g_cloud_map[credential.id]["keyname_list"] = credential["available_keys"];
            }
        }

        for(var site_name in g_cloud_map) {
            var status = null;
            var credentials = g_cloud_map[site_name];

            if (!credentials["key_name"] && !credentials["access_key"] && !credentials["secret_key"]) {
                status = "Disabled";
            }
            else if (!credentials["key_name"]) {
                status = "Incomplete";
            }
            else {
                status = "Enabled";
            }
            $("#cloud_table_body").append(make_cloud_table_row(site_name, status));
        }
        phantom_cloud_edit_change_cloud_internal();
        phantom_cloud_edit_enable(true);
    };

    var sites_loaded = function(sites) {

        g_cloud_map = {};

        for (var i = 0; i < sites.length; i++) {
            var site = sites[i];
            if (site.hasOwnProperty("id")) {
                g_cloud_map[site.id] = {}
            }
        }

    }

    var sites_url = make_url('sites');
    var sites_request = phantomGET(sites_url);

    var credentials_url = make_url('credentials/sites?details=true');
    var credentials_request = phantomGET(credentials_url);

    $.when(sites_request, credentials_request)
        .done(function(sites, credentials) {
            sites_loaded(sites[0]);
            credentials_loaded(credentials[0]);
        })
        .fail(function(sites_err, credentials_err) {
            phantom_alert("Problem getting credentials: " + sites_err.responseText + credentials_err.responseText);
            phantom_cloud_edit_enable(true);
        });

    phantom_cloud_edit_enable(false);
}

function phantom_cloud_edit_load_page() {
    try {
        phantom_cloud_edit_enable(false);
        phantom_cloud_edit_load_sites();
    }
    catch(err) {
        phantom_alert(err);
    }
}

function phantom_cloud_edit_remove_click() {
    var cloud_name = $("#cloud_table_body tr.info td").first().text();
    var q = "Are you sure you want to remove the cloud ".concat(cloud_name).concat(" from your configuration?");
    var doit = confirm(q);

    if (!doit) {
        return;
    }

    var url = make_url("credentials/sites/" + cloud_name);

    var success_func = function (obj) {
        $("#phantom_cloud_edit_name").empty();
        $("#phantom_cloud_edit_access").val("");
        $("#phantom_cloud_edit_secret").val("");
        $("#phantom_cloud_edit_keyname_list").empty();

        phantom_cloud_edit_load_sites();
    }

    var error_func = function(obj, message) {
        phantom_alert(message);
        phantom_cloud_edit_enable(true);
    }

    phantom_cloud_edit_enable(false);
    phantomDELETE(url, success_func, error_func);
}
