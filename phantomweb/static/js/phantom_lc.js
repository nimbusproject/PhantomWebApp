var g_cloud_map = {};
var g_arranged_cloud_values = {};
var g_lc_info = {};
var g_blank_name = "<new name>";

function phantom_lc_buttons(enabled) {

    if (enabled) {
        $("#phantom_lc_name_select").removeAttr("disabled", "disabled");
        $("#phantom_lc_delete").removeAttr("disabled", "disabled");
        $("#phantom_lc_save").removeAttr("disabled", "disabled");
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
        $("#phantom_lc_name_select").attr("disabled", "disabled");
        $("#phantom_lc_delete").attr("disabled", "disabled");
        $("#phantom_lc_save").attr("disabled", "disabled");
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


function phantom_lc_reload_success_func(obj) {
    try {
        $("#phantom_lc_cloud").empty();
        g_cloud_map = obj.cloud_info;
        g_lc_info = obj.lc_info;

        phantom_lc_load_lc_names();
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

function phantom_lc_load_error_func(obj, message) {
    phantom_lc_buttons(true);
    alert(message);
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

    if (cloud_name == undefined || cloud_name == null || cloud_name == "") {
        return;
    }
    var cloud_data = g_cloud_map[cloud_name];

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

    for(var site in g_cloud_map) {
        var cloud_data = g_cloud_map[site];
        if (cloud_data.status != 0) {
            alert("There was an error communication with ".concat(site).concat(".  You may interact with the remaining clouds.  Refresh later when the cloud is available."))        }
        else {
            var new_opt = $('<option>', {'name': site, value: site, text: site});
            $("#phantom_lc_cloud").append(new_opt);
        }
    }
}

function phantom_lc_load_lc_names() {
    $("#phantom_lc_name_select")

    var ordered = Array();
    var new_opt = $('<option>', {'name': g_blank_name, value: g_blank_name, text: g_blank_name});
    $("#phantom_lc_name_select").append(new_opt);

    for (var lc_name in  g_lc_info) {
        var lc = g_lc_info[lc_name];
        var rank = lc["rank"];
        ordered[rank - 1] = lc;
    }

    for(lc in ordered) {
        var new_opt = $('<option>', {'name': lc_name, value: lc_name, text: lc_name});
        $("#phantom_lc_name_select").append(new_opt);
    }
}

function phantom_lc_change_lc_internal() {
    var lc_name =  $("#phantom_lc_name_select").val();

    if (lc_name == g_blank_name) {
        // set to blank values
        g_arranged_cloud_values = {};
        $("#phantom_lc_name_input").val("");
        $("#phantom_lc_name_input").text("");
    }
    else {
        $("#phantom_lc_name_input").val(lc_name);
        $("#phantom_lc_name_input").text(lc_name);
        g_arranged_cloud_values = g_lc_info[lc_name];
    }

    $("#phantom_lc_order").empty();
    for (var site in g_arranged_cloud_values) {
        var new_opt = $('<option>', {'name': site, value: site, text: site});
        $("#phantom_lc_order").append(new_opt);
    }
}

function phantom_lc_change_lc_click() {
    try {
        phantom_lc_change_lc_internal();
    }
    catch(err) {
        alert(err);
    }
}

function phantom_lc_load_internal() {
    var url = make_url('api/launchconfig/load')
    phantom_lc_buttons(false);
    phantomAjaxPost(url, {}, phantom_lc_reload_success_func, phantom_lc_load_error_func);
}

function phantom_lc_load() {
    try {
        phantom_lc_load_internal();
    }
    catch(err) {
        alert(err);
    }
}

function phantom_lc_add_click() {
    var cloud_name = $("#phantom_lc_cloud").val().trim();
    var max_vm = $("#phantom_lc_max_vm").val().trim();
    var instance_type = $("#phantom_lc_instance").val().trim();
    var keyname = $("#phantom_lc_keyname").val().trim();

    var common;
    var image_id = "";
    if ($("#phantom_lc_common_choice_checked").is(':checked')) {
        image_id = $("#phantom_lc_common_images_choices").val().trim();
        common = true;
    }
    else {
        image_id = $("#phantom_lc_user_images_choices").val().trim();
        common = false;
    }

    if (cloud_name == undefined || cloud_name == "") {
        alert("You must select a cloud.");
        return;
    }
    if (max_vm == undefined || max_vm == "") {
        alert("You must select a maximum number of VMs for this cloud.");
        return;
    }
    if (image_id == undefined || image_id == "") {
        alert("You must select a image.");
        return;
    }
    if (instance_type == undefined || instance_type == "") {
        alert("You must select an instance type.");
        return;
    }
    if (keyname == undefined || keyname == "") {
        alert("You must select a key name.");
        return;
    }
    if (max_vm < -1 || max_vm > 32000) {
        alert("You must specify a maximum number of VMs between -1 (infinity) and 32000.");
        return;
    }

    var entry = {
        'cloud': cloud_name,
        'max_vm': max_vm,
        'image_id': image_id,
        'instance_type': instance_type,
        'keyname': keyname,
        'common': common,
        'user_data': $("#phantom_lc_userdata").val()
    };

    g_arranged_cloud_values[cloud_name] = entry;

    $("#phantom_lc_order option[value='".concat(cloud_name).concat("']")).remove();

    var new_opt = $('<option>', {'name': cloud_name, value: cloud_name, text: cloud_name});
    $("#phantom_lc_order").append(new_opt);
}

function phantom_lc_save_click_internal() {
    var lc_name = $("#phantom_lc_name_input").val();

    var err_msg = undefined;
    if (lc_name == undefined || lc_name == "") {
        err_msg = "You must select a launch configuration name."
    }

    if (err_msg != undefined) {
        alert(err_msg);
        return;
    }

    var data = {'name': lc_name};

    $('#phantom_lc_order option').each(function(i, option) {

        var site_name = option.value;
        var cloud_data = g_arranged_cloud_values[site_name];

        var rank_key = site_name.concat(".").concat("rank");
        var cloud_key = site_name.concat(".").concat("cloud");
        var keyname_key = site_name.concat(".").concat("keyname");
        var image_id_key = site_name.concat(".").concat("image_id");
        var instance_type_key = site_name.concat(".").concat("instance_type");
        var max_vm_key = site_name.concat(".").concat("max_vm");
        var common_key = site_name.concat(".").concat("common");

        var ndx = i + 1;

        data[rank_key] = ndx;
        data[cloud_key] = cloud_data["cloud"];
        data[keyname_key] = cloud_data["keyname"];
        data[image_id_key] = cloud_data["image_id"];
        data[instance_type_key] = cloud_data["instance_type"];
        data[max_vm_key] = cloud_data["max_vm"];
        data[common_key] = cloud_data["common"];
    });

    var success_func = function(obj) {
        phantom_lc_load_internal();
    }

    var error_func = function(obj, message) {
        phantom_lc_buttons(true);
    }

    var url = make_url("api/launchconfig/save");
    phantomAjaxPost(url, data, success_func, error_func);
    phantom_lc_buttons(false);
}

function phantom_lc_save_click() {
    try {
        phantom_lc_save_click_internal();
    }
    catch (err) {
        alert(err);
    }
}

function phantom_lc_delete_internal(lc_name) {

    var success_func = function(obj) {
        phantom_lc_load_internal();
    }

    var error_func = function(obj, message) {
        phantom_lc_buttons(true);
    }

    var url = make_url("api/launchconfig/delete");
    var data = {"name": lc_name};

    $("#phantom_lc_name_select").empty();
    phantom_lc_buttons(false);
    phantomAjaxPost(url, data, success_func, error_func);
}

function phantom_lc_delete_click() {

    var lc_name = $("#phantom_lc_name_select").val();

    var q = "Are you sure you want to delete the launch configuration ".concat(lc_name).concat("?");
    var doit = confirm(q);
    if(!doit) {
        return;
    }

    try {
        phantom_lc_delete_internal(lc_name);
    }
    catch (err) {
        alert(err);
    }
}

function phantom_lc_remove_click() {
    var cloud_name = $("#phantom_lc_order").val();
    $("#phantom_lc_order option:selected").remove();
    delete g_arranged_cloud_values[cloud_name];
}

function phantom_lc_up_click() {
    $('#phantom_lc_order option:selected').each(function(){
        $(this).insertBefore($(this).prev()) });
}

function phantom_lc_down_click() {
    $('#phantom_lc_order option:selected').each(function(){
            $(this).insertAfter($(this).next()); });
}

function phantom_lc_cloud_selected_click() {
    try {
        var cloud_name = $("#phantom_lc_order").val();
        var cloud_val_dict = g_arranged_cloud_values[cloud_name];

        $("#phantom_lc_cloud").val(cloud_val_dict['cloud']);

        phantom_lc_select_new_cloud_internal();

        $("#phantom_lc_max_vm").val(cloud_val_dict['max_vm']);
        $("#phantom_lc_instance").val(cloud_val_dict['instance_type']);
        $("#phantom_lc_keyname").val(cloud_val_dict['keyname']);
        $("#phantom_lc_userdata").val(cloud_val_dict['user_data']);

        if (cloud_val_dict['common']) {
            $("#phantom_lc_common_images_choices").val(cloud_val_dict['image_id']);
            $("#phantom_lc_common_choice_checked").attr('checked',true);
        }
        else {
            $("#phantom_lc_user_images_choices").val(cloud_val_dict['image_id']);
            $("#phantom_lc_user_choice_checked").attr('checked',true);
        }
        phantom_lc_change_image_type();
    }
    catch (err) {
        alert("There was a problem loading the page.  Please try again later. ".concat(err.message));
    }
}