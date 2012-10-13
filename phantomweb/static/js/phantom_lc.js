var cloud_map = {};
var g_arranged_cloud_values = {};

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

function phantom_lc_add_click() {
    var cloud_name = $("#phantom_lc_cloud").val().trim();
    var max_vm = $("#phantom_lc_max_vm").val().trim();
    var instance_type = $("#phantom_lc_instance").val().trim();
    var keyname = $("#phantom_lc_keyname").val().trim();

    var common;
    var image = "";
    if ($("#phantom_lc_common_choice_checked").is(':checked')) {
        image = $("#phantom_lc_common_images_choices").val().trim();
        common = true;
    }
    else {
        image = $("#phantom_lc_user_images_choices").val().trim();
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
    if (image == undefined || image == "") {
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
        'image': image,
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
            $("#phantom_lc_common_images_choices").val(cloud_val_dict['image']);
            $("#phantom_lc_common_choice_checked").attr('checked',true);
        }
        else {
            $("#phantom_lc_user_images_choices").val(cloud_val_dict['image']);
            $("#phantom_lc_user_choice_checked").attr('checked',true);
        }
        phantom_lc_change_image_type();
    }
    catch (err) {
        alert("There was a problem loading the page.  Please try again later. ".concat(err.message));
    }
}