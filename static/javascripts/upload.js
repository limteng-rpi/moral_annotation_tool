/**
 * Created by limteng on 5/21/17.
 */
$(document).on('submit', '#upload-form', function(e) {
    e.preventDefault();
    // check values
    var dataset = $('input[name="dataset"]').val().trim();
    if (dataset.length > 0) {
        if(document.getElementById("input-file").files.length === 0) {
            $('#msg').text('Data file not selected').show()
        } else {
            $('#msg').hide();
            var form_data = new FormData($(this)[0]);
            $.ajax({
                url: '/upload',
                processData: false,
                data: form_data,
                type: 'POST',
                cache: false,
                contentType: false,
                success: function (response) {
                    console.log(response);
                }
            });
        }
    } else {
        $('#msg').text('Empty dataset name').show()
    }
    return false;
});