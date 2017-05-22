/**
 * Created by limteng on 5/21/17.
 */
$(document).on('click', 'button#reg-btn', function () {
    var username = $('input#input-username').val();
    var password = $('input#input-password').val();
    var firstname = $('input#input-firstname').val();
    var lastname = $('input#input-lastname').val();
    $.post('/register', {
        username: username,
        password: password,
        firstname: firstname,
        lastname: lastname
    }, function (response) {
        if (response.code === 200) {
            window.location.replace('/login');
        } else {
            $('#msg').text(response.msg).show();
        }
    }, 'json')
});