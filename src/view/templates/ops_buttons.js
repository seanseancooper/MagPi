<script>
    function setsHeaders(xhttp) {
        xhttp.setRequestHeader('Access-Control-Allow-Origin', 'localhost:*');
        xhttp.setRequestHeader('Access-Control-Allow-Methods', 'POST');
        xhttp.setRequestHeader('Content-Type', 'text/html');
        xhttp.setRequestHeader('Access-Control-Allow-Headers', 'Content-Type, Access-Control-*');
    }

    function add(uniqId, trgt){
        var xhttp = new XMLHttpRequest();
        xhttp.open("POST", "{{ url_for('.index')}}add/" + uniqId, true);
        setsHeaders(xhttp);
        xhttp.setRequestHeader('TARGET', trgt);
        xhttp.send();

        xhttp.onload = function() {
            const resp = xhttp.response;
            var aButton = document.getElementById("add_button_" + uniqId);
            if (resp == "OK"){
                aButton.classList.value = "adding_button";
                aButton.innerHTML = "------";
                setTimeout(function() {
                    aButton.classList.value = "add_btn added_button";
                    aButton.innerHTML = "ADDED";
                }, 250);
            } else {
                aButton.classList.value = "adding_failed_button";
                aButton.innerHTML = "FAILED!";
            };
        };
    }

    function mute(uniqId, trgt){
        var xhttp = new XMLHttpRequest();

        xhttp.open("POST", "{{ url_for('.index')}}mute/" + uniqId, true);
        setsHeaders(xhttp);
        xhttp.setRequestHeader('TARGET', trgt);
        xhttp.send();

        xhttp.onload = function() {
            const resp = xhttp.response;
            var mButton = document.getElementById("mute_button_" + uniqId);

            if (resp == "False"){
                mButton.classList.value = "muting_button";
                mButton.innerHTML = "------";
                setTimeout(function() {
                    mButton.classList.value = "mute_btn unmute_button";
                    mButton.innerHTML = "MUTE";
                }, 250);
            }

            if (resp == "True"){
                mButton.classList.value = "muting_button";
                mButton.innerHTML = "------";
                setTimeout(function() {
                    mButton.classList.value = "mute_btn mute_button";
                    mButton.innerHTML = "UNMUTE";
                }, 250);
            };
        };
    }

    function remove(uniqId, trgt){
        var xhttp = new XMLHttpRequest();
        xhttp.open("POST", "{{ url_for('.index')}}remove/" + uniqId, true);
        setsHeaders(xhttp);
        xhttp.setRequestHeader('TARGET', trgt);
        xhttp.send();

        xhttp.onload = function() {
            const resp = xhttp.response;
            rButton = document.getElementById("remove_button_" + uniqId);
            if (resp == "OK"){
                rButton.classList.value = "rem_button";
                rButton.style = "color:white;";
                rButton.innerHTML = "*";
                setTimeout(function() {
                    mButton = document.getElementById("mute_button_" + uniqId);
                    uButton = document.getElementById("unmute_button_" + uniqId);

                    if (mButton) {
                            mButton.style = "display:none;"
                    };

                    if (uButton) {
                            uButton.style = "display:none;"
                    };

                    // note width increase
                    rButton.classList.value = "rem_button removed_button button";
                    rButton.innerHTML = "REMOVED";

                }, 250);
            } else {
                rButton.classList.value = "remove_failed_button";
                rButton.innerHTML = "x";
            };
        };
    }

    function write_tracked(button, trgt){

        var xhttp = new XMLHttpRequest();

        xhttp.open('POST', "{{ url_for('.index')}}write", true);
        setsHeaders(xhttp);
        xhttp.setRequestHeader('TARGET', trgt);
        xhttp.send();

        xhttp.onload = function() {
            button.innerHTML = (xhttp.response == "OK")? "DONE": "FAILED";
        };
    }

    function select_all(button, trgt){
        // not sure how this should work yet
        alert('select all: ' + trgt);
    }

    function select_none(button, trgt){
    // not sure how this should work yet
        alert('select none: ' + trgt);
    }
</script>
