/**
 * Created by limteng on 5/21/17.
 */
$(document).on('click', 'button#login-btn', function () {
    var username = $('input#input-username').val();
    var password = $('input#input-password').val();
    $.post('/login', {
        username: username,
        password: password
    }, function (response) {
        if (response.code == 200) {
            var redirect_url = get_parameter_by_name('redirect');
            if (typeof redirect_url !== 'undefined' && redirect_url.length > 0) {
                window.location.replace(redirect_url);
            } else {
                window.location.replace('/');
            }
        } else {
            $('#msg').text(response.msg).show();
        }
    }, 'json')
});

function get_parameter_by_name(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return undefined;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}