var available_launch_configs = {};
var user_launch_configs = [];
var lc_to_import = null;

$(document).ready(function() {
    $("#nav-appliances").addClass("active");

    $("#public_lc_table > tr").hide();
    $("#show-all-lc").hide();
    load_public_lcs();

    $("a.lc_id").click(function() {
        return false;
    });

    $("#show-all-lc").click(function() {
        window.location.hash = '';
        return false;
    });

    $("#public_lc_table").on("click", "button.import", function() {
        lc_to_import = $(this).data('name');
        $('#import-lc-modal').modal('show');
        return false;
    });

    $("#import-lc-modal").on('shown', function() {
        $("#import-lc-name").focus();
        var lc = available_launch_configs[lc_to_import];
        if (lc && lc.name &&  user_launch_configs.indexOf(lc.name) < 0) {
            $("#import-lc-name").val(lc.name);
            $("#import-lc-name").select();
        }
    });

    var import_lc_verify = function() {
        $(".help-inline").remove();
        $import_lc_name = $("#import-lc-name");

        var newname = $import_lc_name.val();
        $import_lc_name.parent().parent().removeClass('error');

        if (user_launch_configs.indexOf(newname) > -1) {
            $import_lc_name.parent().parent().addClass("error");
            $import_lc_name.after("<span class='help-inline'>You already have a Launch Config by this name.</span>");
            return false;
        }
        $('a').addClass('disabled');
        $import_lc_name.parent().parent().hide()
        $("#importing").show();
        import_lc(lc_to_import, newname);
        return false;
    };

    $("#import-launch-configuration").click(function() {
        import_lc_verify();
    });

    $("#add-lc-form").submit(function() {
        import_lc_verify();
        return false;
    });

    $(window).on('hashchange', function() {
        select_from_hash();
    });
});


function load_public_lcs() {

    var load_all_lc_success = function(launchconfigs) {

        for (var i=0; i<launchconfigs.length; i++) {
            var lc = launchconfigs[i];
            user_launch_configs.push(lc.name);
        }
    }

    var load_lc_success = function(launchconfigs) {
        for (var i=0; i<launchconfigs.length; i++) {
            var lc = launchconfigs[i];
            available_launch_configs[lc.id] = lc;
            make_lc_row(lc);
        }

        select_from_hash();
        $("#loading").hide();

        var lc_url = make_url('launchconfigurations')
        phantomGET(lc_url, load_all_lc_success, load_lc_failure);
    }

    var load_lc_failure = function(error) {
        console.log(error);
    }

    var lc_url = make_url('launchconfigurations?public=true')
    phantomGET(lc_url, load_lc_success, load_lc_failure);
}

function import_lc(lc_id_to_import, new_name) {
    var import_lc_success = function(imported_lc) {
        window.location.href = "/phantom/launchconfig#" + imported_lc.name;
    }

    var import_lc_failure = function(url, error) {
        phantom_alert("Problem importing launch config! " + error);
        $('a').removeClass('disabled');
        $import_lc_name.parent().parent().show()
        $("#importing").hide();
    }

    var lc_to_import = available_launch_configs[lc_id_to_import];
    delete lc_to_import['id'];
    delete lc_to_import['url'];
    delete lc_to_import['owner'];
    delete lc_to_import['description'];
    lc_to_import['appliance'] = lc_to_import['name'];
    lc_to_import['name'] = new_name;

    var url = make_url("launchconfigurations");
    console.log(lc_to_import);
    phantomPOST(url, lc_to_import, import_lc_success, import_lc_failure);
    $("#row-" + lc_id_to_import + " button.import").html("Importing...");
}


function make_lc_row(lc) {

    var row = "<tr id='row-" + lc.id + "'>" +
        "<td><p class='lead'><a class='lc_id' href='#" + lc.id + "'>" + lc.name + "</a></p>" +
        "<p>By " + lc.owner + "</p>" +
        "<p><button class='btn btn-small import' data-name='" + lc.id + "'>Import</button></p></td>" +
        "<td><p class='lead'>&nbsp;</p><p>" + lc.description + "</td>" +
        "</tr>";
    $("#public_lc_table").append(row);
}

function select_from_hash() {
    var url_id = window.location.hash.substring(1);
    if (available_launch_configs.hasOwnProperty(url_id)) {
        $("#public_lc_table tr").hide();
        $("#row-" + url_id).show();
        $("#show-all-lc").show();
    }
    else { // Default
        $("#public_lc_table tr").show();
        $("#show-all-lc").hide();
    }
}
