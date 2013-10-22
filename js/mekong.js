function openSignInModal() {
    $("#registerModal").modal("hide");
    $("#signInModal").modal();
}

function openRegisterModal() {
    $("#signInModal").modal("hide");
    $("#registerModal").modal();
}

function displaySignInFailed(problem) {
    $("#signInAlert").text(problem);
    $("#signInAlert").show();
    $("#signInModal").modal();
}

function displayRegisterFailed(problem) {
    $("#registerAlert").text(problem);
    $("#registerAlert").show();
    $("#registerModal").modal();
}
