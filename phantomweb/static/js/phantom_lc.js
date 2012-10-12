var cloud_map = {};

function phantom_lc_buttons(enabled) {

    if (enabled) {
        $("#phantom_lc_cloud").removeAttr("disabled", "disabled");
        $("#phantom_lc_max_vm").removeAttr("disabled", "disabled");
        $("#phantom_lc_instance").removeAttr("disabled", "disabled");
        $("#phantom_lc_keyname").removeAttr("disabled", "disabled");
        $("#phantom_lc_userdata").removeAttr("disabled", "disabled");
        $("#phantom_lc_add").removeAttr("disabled", "disabled");
        $("#phantom_lc_remove").removeAttr("disabled", "disabled");
        $("#phantom_lc_up").removeAttr("disabled", "disabled");
        $("#phantom_lc_down").removeAttr("disabled", "disabled");
        phantom_lc_change_image_type();
        $('#phantom_lc_loading_image').hide();
    }
    else {
        $("#phantom_lc_cloud").attr("disabled", "disabled");
        $("#phantom_lc_max_vm").attr("disabled", "disabled");
        $("#phantom_lc_instance").attr("disabled", "disabled");
        $("#phantom_lc_keyname").attr("disabled", "disabled");
        $("#phantom_lc_common_images_choices").attr("disabled", "disabled");
        $("#phantom_lc_user_images_choices").attr("disabled", "disabled");
        $("#phantom_lc_userdata").attr("disabled", "disabled");
        $("#phantom_lc_add").attr("disabled", "disabled");
        $("#phantom_lc_remove").attr("disabled", "disabled");
        $("#phantom_lc_up").attr("disabled", "disabled");
        $("#phantom_lc_down").attr("disabled", "disabled");
        $('#phantom_lc_loading_image').show();
    }

}

function phantom_lc_select_new_cloud() {
    try
    {
        phantom_lc_select_new_cloud_internal();
    }
    catch(err)
    {
        alert("There was a problem on the page.  ".concat(err.message));
        $('#phantom_lc_loading_image').hide();
    }
    phantom_lc_buttons(true);
}

function phantom_lc_change_image_type() {
    if ($("#phantom_lc_common_choice_checked").is(':checked')) {
        $("#phantom_lc_common_images_choices").removeAttr("disabled", "disabled");
        $("#phantom_lc_user_images_choices").attr("disabled", "disabled");
    }
    else {
        $("#phantom_lc_user_images_choices").removeAttr("disabled", "disabled");
        $("#phantom_lc_common_images_choices").attr("disabled", "disabled");
    }
}

function phantom_lc_select_new_cloud_internal() {
    var cloud_name = $("#phantom_lc_cloud").val();
    var cloud_data = cloud_map[cloud_name];

    if (cloud_data.status != 0) {
        return;
    }
    $("#phantom_lc_keyname").empty();
    for (key in cloud_data.keynames) {
        var keyname = cloud_data.keynames[key];
        var new_opt = $('<option>', {'name': keyname, value: keyname, text: keyname});
        $("#phantom_lc_keyname").append(new_opt);
    }
    $("#phantom_lc_instance").empty();
    for (instance in cloud_data.instances) {
        var i = cloud_data.instances[instance];
        var new_opt = $('<option>', {'name': i, value: i, text: i});
        $("#phantom_lc_instance").append(new_opt);
    }
    $("#phantom_lc_common_images_choices").empty();
    for (public in cloud_data.public_images) {
        var i = cloud_data.public_images[public];
        var new_opt = $('<option>', {'name': i, value: i, text: i});
        $("#phantom_lc_common_images_choices").append(new_opt);
    }
    $("#phantom_lc_user_images_choices").empty();
    for (personal in cloud_data.personal_images) {
        var i = cloud_data.personal_images[personal];
        var new_opt = $('<option>', {'name': i, value: i, text: i});
        $("#phantom_lc_user_images_choices").append(new_opt);
    }
}

function phantom_lc_load_cloud_names() {

    for(var site in cloud_map) {
        var cloud_data = cloud_map[site];
        if (cloud_data.status != 0) {
            alert("There was an error communication with ".concat(site).concat(".  You may interact with the remaining clouds.  Refresh later when the cloud is available."))        }
        else {
            var new_opt = $('<option>', {'name': site, value: site, text: site});
            $("#phantom_lc_cloud").append(new_opt);
        }
    }
}

function phantom_lc_load() {

    var url = make_url('load_lc')

    var success_func = function (obj) {
        try {
            cloud_map = obj.cloud_info;
            phantom_lc_load_cloud_names()
            phantom_lc_select_new_cloud_internal();
            phantom_lc_change_image_type();
            phantom_lc_buttons(true);
        }
        catch (err) {
            alert("There was a problem loading the page.  Please try again later. ".concat(err.message));
            $('#phantom_lc_loading_image').hide();
        }
    }

    var error_func = function(obj, message) {
        phantom_lc_buttons(true);
        alert(message);
    }

    phantom_lc_buttons(false);
    phantomAjaxPost(url, {}, success_func, error_func);

}