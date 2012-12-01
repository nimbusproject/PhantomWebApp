var g_cloud_map = {};

$(document).ready(function() {
    $("#nav-clouds").addClass("active");
});

function phantom_cloud_edit_enable(enable) {
    if(enable) {
        $("#phantom_cloud_edit_add").removeAttr("disabled", "disabled");
        $("#phantom_cloud_edit_remove").removeAttr("disabled", "disabled");
        $('#phantom_cloud_edit_name').removeAttr("disabled", "disabled");
        $('#phantom_cloud_edit_loading_image').hide();
    }
    else {
        $("#phantom_cloud_edit_add").attr("disabled", "disabled");
        $("#phantom_cloud_edit_remove").attr("disabled", "disabled");
        $("#phantom_cloud_edit_name").attr("disabled", "disabled");
        $('#phantom_cloud_edit_loading_image').show();
        $("#phantom_cloud_edit_access").val("");
        $("#phantom_cloud_edit_secret").val("");
        $("#phantom_cloud_edit_keyname_list").empty();
    }
}


function phantom_cloud_edit_add_click() {

    var nameCtl = $("#phantom_cloud_edit_name").val().trim();
    var accessCtl = $("#phantom_cloud_edit_access").val().trim();
    var secretCtl = $("#phantom_cloud_edit_secret").val().trim();
    var keyCtl = $("#phantom_cloud_edit_keyname_list").val();

    var error_msg = undefined;
    if(nameCtl == undefined || nameCtl == "") {
        error_msg = "You must name your cloud."
    }
    if(accessCtl == undefined || accessCtl == "") {
        error_msg = "You must provide a EC2 compatible access key query token";
    }
    if(secretCtl == undefined || secretCtl == "") {
        error_msg = "You must provide a EC2 compatible secret key query token";
    }
    if(keyCtl == undefined) {
        keyCtl = "";
    }

    if (error_msg != undefined) {
        alert(error_msg);
    }

    //send call to service
    var success_func = function (obj) {
        $("#phantom_cloud_edit_list").empty();
        $("#phantom_cloud_edit_name").empty();
        $("#phantom_cloud_edit_access").val("");
        $("#phantom_cloud_edit_secret").val("");
        $("#phantom_cloud_edit_keyname_list").empty();

        phantom_cloud_edit_load_sites();
    }

    var error_func = function(obj, message) {
        alert(message);
        phantom_cloud_edit_enable(true);
    }

    var url = make_url('api/sites/add');
    phantom_cloud_edit_enable(false);
    phantomAjaxPost(url, {'cloud': nameCtl, 'access': accessCtl, 'secret': secretCtl, 'keyname': keyCtl}, success_func, error_func);
}


function phantom_cloud_edit_change_cloud_internal ()  {
    var selected_cloud_name = $("#phantom_cloud_edit_name").val();
    var val = g_cloud_map[selected_cloud_name];

    $("#phantom_cloud_edit_key_message").text("");
    $("#phantom_cloud_edit_keyname_list").empty();
    $("#phantom_cloud_edit_status").text("");
    if (val == undefined) {
        $("#phantom_cloud_edit_access").val("");
        $("#phantom_cloud_edit_secret").val("");
        $("#phantom_cloud_edit_status").text("Add your credentials and save this cloud.  Then add a key.");
    }
    else {
        $("#phantom_cloud_edit_access").val(val['access_key']);
        $("#phantom_cloud_edit_secret").val(val['secret_key']);
        $("#phantom_cloud_edit_status").val(val.status_msg);
        $("#phantom_cloud_edit_status").text(val.status_msg);
        for (keyndx in val.keyname_list) {
            $("#phantom_cloud_edit_key_message").val("");
            key = val.keyname_list[keyndx]
            var new_choice = $('<option>',  {'name': key, value: key, text: key});
            $("#phantom_cloud_edit_keyname_list").append(new_choice);
        }
        if(val.keyname == undefined || val.keyname == "") {
            $("#phantom_cloud_edit_key_message").text("There is no key set for this cloud.  Please select one and click \"Add\"");
        }
        else {
            $("#phantom_cloud_edit_keyname_list").val(val.keyname);
        }
    }
}

function phantom_cloud_edit_change_cloud ()  {
    try {
        phantom_cloud_edit_change_cloud_internal();
    }
    catch(err) {
        alert(err);
    }
}

function phantom_cloud_edit_load_sites() {
    var url = make_url('api/sites/load');

    var success_func = function(obj){

        phantom_cloud_edit_enable(true);
        var selected_cloud_name = $("#phantom_cloud_edit_name").val();
        for(var site in obj.sites) {
            g_cloud_map = obj.sites;
            var new_opt = $('<li>', {'name': site});
            new_opt.text(site);
            $("#phantom_cloud_edit_list").append(new_opt);
        }
        for(var site in obj.all_sites) {
            site = obj.all_sites[site];
            var new_choice = $('<option>',  {'name': site, value: site, text: site});
            $("#phantom_cloud_edit_name").append(new_choice);
        }
        phantom_cloud_edit_change_cloud_internal();
    };

    var error_func = function(obj, error_msg) {
        alert(error_msg);
        phantom_cloud_edit_enable(true);
    };

    $("#phantom_cloud_edit_list").children().remove();
    phantom_cloud_edit_enable(false);
    ajaxCallREST(url, success_func, error_func);
}

function phantom_cloud_edit_load_page() {
    try {
        phantom_cloud_edit_enable(false);
        phantom_cloud_edit_load_sites();
    }
    catch(err) {
        alert(err);
    }
}

function phantom_cloud_edit_remove_click() {
    var cloud_name = $("#phantom_cloud_edit_name").val();
    var q = "Are you sure you want to remove the cloud ".concat(cloud_name).concat(" from your configuration?");
    var doit = confirm(q);

    if (!doit) {
        return;
    }

    var url = make_url("api/sites/delete");
    url = url.concat("?cloud=").concat(cloud_name);

    var success_func = function (obj) {
        $("#phantom_cloud_edit_list").empty();
        $("#phantom_cloud_edit_name").empty();
        $("#phantom_cloud_edit_access").val("");
        $("#phantom_cloud_edit_secret").val("");
        $("#phantom_cloud_edit_keyname_list").empty();

        phantom_cloud_edit_load_sites();
    }

    var error_func = function(obj, message) {
        alert(error_msg);
        phantom_cloud_edit_enable(true);
    }

    phantom_cloud_edit_enable(false);
    ajaxCallREST(url, success_func, error_func);
}
