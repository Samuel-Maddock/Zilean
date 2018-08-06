$.ajaxSetup({
    async: false
  });

function onAboutClick(){
    $("#about-button").click(function() {
        $("#about-modal").show();
        $("body").addClass("modal-open");
    });

    $("#about-close").click(function(){
        $("#about-modal").hide();
        $("body").removeClass("modal-open")
    });

    // Command image modal close button
    $("#command-modal-close").click(function(){
        $("#command-modal").hide();
    });

    $("#command-modal-background").click(function(){
        $("#command-modal").hide();
    });
}

function initTabs(){
    var keys
    $.getJSON("commandList.json", function(json){
        keys = Object.keys(json)
        var html = ""
        keys.forEach(key => {
            name = key.replace(/([A-Z])/g, ' $1').trim()
            if (key == "UtilityCommands"){
                html+="<li id=" + key + " class='is-active tab-item'><a>" + name + "</a></li>"
            } else{
                html += "<li id=" + key + " class='tab-item'><a>" + name + "</a></li>"
            }
        });
        $("#tab-list").append(html)
    });
    return keys
}

function imageOnClick(command){
    $("#" + command).click(function(){
        $("#command-modal-image").attr("src", "assets/commands/~" + command + ".png");
        $("#command-modal").show();
    });
}

function createTable(key){
    $.getJSON("commandList.json", function(json) {
        arr = json[key]
        
        var html = ""
        var command = ""
        arr.forEach(element => {
            command = element[0].substr(1).replace(/\s+/g, '-')
            html +='<tr id="' + command + '"><td>' + element[0] + '</td><td>';
            if (element[1].length > 1) {
                for(i = 0; i < element[1].length; i++){
                    if (i>0){
                        html += "<br/><br/>" + element[1][i]
                    }else{
                        html += element[1][i]
                    }
                }
            }else{
                html += element[1][0];
            }
            html += '</td><td>' + element[2] + '</td></tr>';
        });
        $('#table-body').append(html); 

        arr.forEach(element=>{
            command = element[0].substr(1).replace(/\s+/g, '-')
            imageOnClick(command)
        })
        
    });
}

function initTabClick(tabKeys){
    tabKeys.forEach(tab => {
        $("#" + tab).click(function() {
            if($("#" + tab).hasClass("is-active")){
                return
            }

            tabKeys.forEach(tab =>{
                $("#" + tab).removeClass("is-active")
            });

            $("#table-body").children().remove()
            $("#" + tab).toggleClass("is-active")
            createTable(tab)
        });
    })
}

$(document).ready(function() {
    onAboutClick();
    tabKeys = initTabs();
    createTable(tabKeys[0]);
    initTabClick(tabKeys);
});