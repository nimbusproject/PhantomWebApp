var available_launch_configs = [];

$(document).ready(function() {

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
        var id = $(this).data('name');
        import_lc(id);
        return false;
    });

    $(window).on('hashchange', function() {
        select_from_hash();
    });
});


function load_public_lcs() {

    var load_lc_success = function(launchconfigs) {
        for (var i=0; i<launchconfigs.length; i++) {
            var lc = launchconfigs[i];
            available_launch_configs[lc.id] = lc;
            make_lc_row(lc);
        }

        select_from_hash();
        $("#loading").hide();
    }

    var load_lc_failure = function(error) {
        console.log(error);
    }

    var lc_url = make_url('launchconfigurations?public=true')
    phantomGET(lc_url, load_lc_success, load_lc_failure);
}

function import_lc(lc_id_to_import) {
    var import_lc_success = function(imported_lc) {
        window.location.href = "/phantom/launchconfig#" + imported_lc.name;
    }

    var import_lc_failure = function(error) {
        phantom_error("Problem importing launch config! " + error);
        console.log(error);
    }

    var lc_to_import = available_launch_configs[lc_id_to_import];
    lc_to_import['name'] = 'import'; //TODO: DELETEME
    delete lc_to_import['id'];
    delete lc_to_import['url'];
    delete lc_to_import['owner'];
    delete lc_to_import['description'];

    var url = make_url("launchconfigurations");
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
