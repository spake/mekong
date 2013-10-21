function openSignInModal() {
    $("#registerModal").modal("hide");
    $("#signInModal").modal();
}

function openRegisterModal() {
    $("#signInModal").modal("hide");
    $("#registerModal").modal();
}

function register() {
    // do client side validation of the inputs

    var problem = "";

    var username = $("#registerForm input[name=username]").val();
    if (username == "") {
        problem = "Please enter a username.";
    } else {

        var password = $("#registerForm input[name=password]").val();
        var password2 = $("#registerForm input[name=password2]").val();
        if (password == "") {
            problem = "Please enter a password.";
        } else if (password != password2) {
            problem = "Make sure both passwords you entered match.";
        }

    }

    if (problem) {
        $("#registerAlert").text(problem);
        $("#registerAlert").fadeIn();
    } else {
        $("#registerAlert").fadeOut();
    }

    return false;
}
