function cloud_edit_disable_buttons(enable) {
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
    }
}


function cloud_edit_add() {

    var nameCtl = $("#phantom_cloud_edit_name").val().trim();
    var accessCtl = $("#phantom_cloud_edit_access").val().trim();
    var secretCtl = $("#phantom_cloud_edit_secret").val().trim();

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

    if (error_msg != undefined) {
        alert(error_msg);
    }

    //send call to service

    var success_func = function (obj) {
        load_sites();
    }

    var error_func = function(obj, message) {
        alert(message);
        cloud_edit_disable_buttons(true);
    }

    var url = make_url('add_cloud');
    cloud_edit_disable_buttons(false);
    phantomAjaxPost(url, {'cloud': nameCtl, 'access': accessCtl, 'secret': secretCtl}, success_func, error_func);
}


function load_sites() {
    var url = make_url('get_user_sites');

    var success_func = function(obj){

        cloud_edit_disable_buttons(true);
        var selected_cloud_name = $("#phantom_cloud_edit_name").val();
        for(var site in obj.sites) {
            if (site == selected_cloud_name) {
                var val = obj.sites[site];
                $("#phantom_cloud_edit_access").val(val['access_key']);
                $("#phantom_cloud_edit_secret").val(val['secret_key']);
            }
            var new_opt = $('<li>', {'name': site});
            new_opt.text(site);
            $("#phantom_cloud_edit_list").append(new_opt);
        }
    };

    var error_func = function(obj, error_msg) {
        alert(error_msg);
        cloud_edit_disable_buttons(true);
    };

    $("#phantom_cloud_edit_list").children().remove();
    cloud_edit_disable_buttons(false);
    ajaxCallREST(url, success_func, error_func);
}

function cloud_edit_loadPage() {
    cloud_edit_disable_buttons(false);
    load_sites();
}

function cloud_edit_load_list_cloud() {
    var cloud_name = $("#phantom_cloud_edit_list").val();
    $("#phantom_cloud_edit_name").val(cloud_name);
    load_sites();
}

function cloud_edit_remove() {
    var cloud_name = $("#phantom_cloud_edit_name").val();
    var q = "Are you sure you want to remove the cloud ".concat(cloud_name).concat(" from your configuration?");
    var doit = confirm(q);

    if (!doit) {
        return;
    }

    var url = make_url("delete_cloud");
    url = url.concat("?cloud=").concat(cloud_name);

    var success_func = function (obj) {
        load_sites();
    }

    var error_func = function(obj, message) {
        alert(error_msg);
        cloud_edit_disable_buttons(true);
    }

    cloud_edit_disable_buttons(false);
    ajaxCallREST(url, success_func, error_func);
}