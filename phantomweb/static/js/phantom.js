function disable_buttons(bool, msg) {
    if(bool) {
        $("#error_status_text").html(msg);
        $("#start_domain_button").attr("disabled", "disabled");
        $("#terminate_domain_button").attr("disabled", "disabled");
        $("#domain_list_choices").attr("disabled", "disabled");
        $("#location_choices").attr("disabled", "disabled");
        $('#main_loading_image').show();
    }
    else {
        $("#error_status_text").html("Ready.");
        $("#start_domain_button").removeAttr("disabled", "disabled");
        $("#terminate_domain_button").removeAttr("disabled", "disabled");
        $("#domain_list_choices").removeAttr("disabled", "disabled");
        $("#location_choices").removeAttr("disabled", "disabled");
        $('#main_loading_image').hide();
    }
}

function make_url(p) {
    var base_url = document.location.href.concat("/");
    return base_url.concat(p);
}

function get_ajax_obj() {
    var ajaxRequest;  // The variable that makes Ajax possible!

    try{
        // Opera 8.0+, Firefox, Safari
        ajaxRequest = new XMLHttpRequest();
    } catch (e){
        // Internet Explorer Browsers
        try{
            ajaxRequest = new ActiveXObject("Msxml2.XMLHTTP");
        } catch (e) {
            try{
                ajaxRequest = new ActiveXObject("Microsoft.XMLHTTP");
            } catch (e){
                // Something went wrong
                alert("Your browser broke!");
                return false;
            }
        }
    }
    return ajaxRequest;
}

function std_error_handler(url, error_msg) {
    var errorOpt = document.getElementById('error_status_text');
    errorOpt.innerText = error_msg;
    alert(error_msg);
    disable_buttons(false, "Ready.")
}

function load_error_handler(url, error_msg) {
    var errorOpt = document.getElementById('error_status_text');
    errorOpt.innerText = error_msg;
    $("#loading_image_div").hide();

    error_msg = error_msg.concat(".  Please refresh later.")
    $("#error_status_text").html(error_msg);
}


function ajaxCallREST(url, func, error_func) {
    var ajaxRequest = get_ajax_obj();
    ajaxRequest.onreadystatechange = function(){
        // We still need to write some code here
        if(ajaxRequest.readyState == 4){
            var error_msg = "";
            if (ajaxRequest.status == 200){
                var obj = eval('(' + ajaxRequest.responseText + ')');
                if(obj.error_message != undefined) {
                    error_msg = obj.error_message;
                }
                else {
                    func(obj);
                }
            }
            else {
                error_msg = ajaxRequest.statusText
            }
            if (error_msg != "") {
                error_func(url, error_msg);
            }
        }
    }
    ajaxRequest.open("GET", url, true);
    ajaxRequest.send(null);
}

function loadDomainBox(obj) {
    var selectOpt = document.getElementById('domain_list_choices');
    selectOpt.options.length = 0;
    for(var i=0; i< obj.domains.length; i++){
        var newOpt = document.createElement('option');
        newOpt.text = obj.domains[i].name;
        newOpt.value = obj.domains[i].name;
        selectOpt.add(newOpt);
    }
}

function populateIaaSCb(obj) {
    var selectOpt = document.getElementById('user_images_choices');
    for(var i=0; i< obj.user_images.length; i++){
        var newOpt = document.createElement('option');
        newOpt.text = obj.user_images[i];
        newOpt.value = obj.user_images[i];
        selectOpt.add(newOpt);
    }
    var selectOpt = document.getElementById('common_images_choices');
    for(var i=0; i< obj.common_images.length; i++){
        var newOpt = document.createElement('option');
        newOpt.text = obj.common_images[i];
        newOpt.value = obj.common_images[i];
        selectOpt.add(newOpt);
    }
}

function ajaxPopulateInitial(url) {

    var func = function(obj){
        populateIaaSCb(obj);
        loadDomainBox(obj);
        $("#loading_image_div").hide();
        $("#phantom_loaded_content").show();

    }
    ajaxCallREST(url, func, load_error_handler);
}

function clear_iaas_inputs() {
    $("#common_images_choices").empty();
    $("#user_images_choices").empty();
}


function populateIaaS() {
    var u = make_url('get_iaas?cloud=');
    var c = document.getElementById('location_choices');
    u = u.concat(c.value);
    var func = function(obj){
        clear_iaas_inputs();
        populateIaaSCb(obj);
        disable_buttons(false);
    }
    disable_buttons(true);
    ajaxCallREST(u, func, std_error_handler);
}

function ajaxGetDomains(url) {

    var func = function(obj){
        loadDomainBox(obj);
        disable_buttons(false);
    }
    disable_buttons(true);
    ajaxCallREST(url, func, std_error_handler);
}

function listAllDomains() {
    var u = make_url('domain/list');
    ajaxGetDomains(u);
}

function startDomain() {
    var asgNameOpt = document.getElementById('domain_name_input');
    var asgSizeOpt = document.getElementById('domain_size_input');
    var allocOpt = document.getElementById('allocation_choices');
    var locationOpt = document.getElementById('location_choices');
    var userImageOpt = document.getElementById('user_images_choices');
    var commonImageOpt = document.getElementById('common_images_choices');
    var whichOpt = document.getElementById('user_choice_checked');

    var common_check = "true";
    if (whichOpt.checked) {
        var image = userImageOpt.value;
        var common_check = "false";
    }
    else {
        var image = commonImageOpt.value;
    }

    var u = make_url('domain/start?');
    u = u.concat('size=').concat(allocOpt.value);
    u = u.concat('&name=').concat(asgNameOpt.value);
    u = u.concat('&image=').concat(image);
    u = u.concat('&cloud=').concat(locationOpt.value);
    u = u.concat('&common=').concat(common_check);
    u = u.concat('&desired_size=').concat(asgSizeOpt.value);

    var func = function(obj){
        listAllDomains();
    }

    disable_buttons(true, "Starting new domain ".concat(asgNameOpt.value).concat("..."));
    ajaxCallREST(u, func, std_error_handler);
}

function deleteDomain() {

    var domainChoiceOpt = document.getElementById('domain_list_choices');

    if (domainChoiceOpt.value == "") {
        alert("You must select a LaunchConfiguration to delete")
        return;
    }
    var url = make_url('domain/delete?name=');
    url = url.concat(domainChoiceOpt.value)

    var rc = confirm('Are you sure you want to delete the Domain '.concat(domainChoiceOpt.value))
    if (rc) {
        var func = function(obj){
            listAllDomains();
        }
        $("#domain_details_name").html("");
        $("#instance_details").empty();
        disable_buttons(true, "Terminating ".concat(domainChoiceOpt.value).concat("..."));
        ajaxCallREST(url, func, std_error_handler);
    }
}

function set_option_box(opt, name) {
    for(var i=0; i < opt.options.length; i++) {
        var x = opt.options[i];
        if (x.text == name) {
            opt.selectedIndex = i;

            return true;
        }
    }
    opt.selectedIndex = -1;
    return false;
}

function loadDomainName() {

    var domainListOpt = document.getElementById('domain_list_choices');
    var url = make_url('domain/list?domain_name=');
    url = url.concat(domainListOpt.value)

    var func = function(obj) {
        var nameOpt = document.getElementById('domain_name_input');
        var desiredSizeOpt = document.getElementById('domain_size_input');

        var domain = null;
        var found = false;
        for(var i=0; i< obj.domains.length; i++){
            if (obj.domains[i].name == domainListOpt.value) {
                domain = obj.domains[i];
                found = true;
            }
        }
        if (found == false){
            disable_buttons(false);
            return;
        }

        var locationOpt = document.getElementById('location_choices');
        var allocOpt = document.getElementById('allocation_choices');
        var userOpt = document.getElementById('user_images_choices');
        var commonOpt = document.getElementById('common_images_choices');
        var commonCheckOpt = document.getElementById('common_choice_checked');
        var userCheckOpt = document.getElementById('user_choice_checked');

        nameOpt.value = domain.name;
        desiredSizeOpt.value = domain.desired_capacity;
        set_option_box(allocOpt, domain.instance_type);
        set_option_box(locationOpt, domain.cloudname);
        var c_rc = set_option_box(commonOpt, domain.image_id);
        var u_rc = set_option_box(userOpt, domain.image_id);
        userCheckOpt.checked = u_rc;
        commonCheckOpt.checked = c_rc;

        $("#domain_details_name").html(domain.name.concat(" instance details."));

        for(var i=0; i< domain.instances.length; i++) {
            var instance = domain.instances[i];

            var fields = new Array();
            fields[0] = instance.lifecycle_state;
            fields[1] = instance.cloud;
            fields[2] = instance.health_status;
            fields[3] = instance.hostname;
            fields[4] = domain.image_id;

            var li = $('<li></li>');
            $("#instance_details").append(li);
            var div = $('<div></div>').addClass('instance_status_div');
            var h4 = $('<h4></h4>').addClass('instance_status_name');
            h4.html(instance.instance_id);
            var ul = $('<ul></ul>').addClass('instance_status_details_list');
            li.append(div);
            div.append(h4);
            div.append(ul);

            for(var j = 0; j < fields.length; j++) {
                var subli = $('<li></li>').addClass('instance_status_details_item');
                subli.html(fields[j]);
                ul.append(subli);
            }
            disable_buttons(false);
        }
    }
    
    var msg = "loading ".concat(domainListOpt.value).concat("...");
    $("#domain_details_name").html(msg);
    $("#instance_details").empty();
    disable_buttons(true, msg);
    ajaxCallREST(url, func, std_error_handler);
}


function loadPage(){
    $("#error_status_text").html("Ready.");
    $("#phantom_loaded_content").hide();
    var u = make_url('get_initial?cloud=');
    var c = document.getElementById('location_choices');
    u = u.concat(c.value);
    ajaxPopulateInitial(u);
}
