$('#fileup').change(function () {
    var res = $('#fileup').val();
    var arr = res.split('\\');
    var filename = arr.slice(-1)[0];
    filextension = filename.split('.');
    filext = '.' + filextension.slice(-1)[0];
    valid = ['.csv'];

    if (valid.indexOf(filext.toLowerCase()) == -1) {
        // File extension is not valid
        $('.imgupload').hide('slow');
        $('.imgupload.ok').hide('slow');
        $('.imgupload.stop').show('slow');

        $('#namefile').css({ color: 'red', 'font-weight': 700 });
        $('#namefile').html('File ' + filename + ' is not a CSV file!');

        $('#submitbtn').hide();
        $('#fakebtn').show();
    } else {
        // File extension is valid
        $('.imgupload').hide('slow');
        $('.imgupload.stop').hide('slow');
        $('.imgupload.ok').show('slow');

        $('#namefile').css({ color: 'green', 'font-weight': 700 });
        $('#namefile').html(filename);

        // Check if the uploaded file has the required columns
        var reader = new FileReader();
        reader.onload = function (e) {
            var contents = e.target.result;
            var lines = contents.split('\n');
            var firstLine = lines[0].trim();
            var columns = firstLine.split(',');

            var requiredColumns = ['Name', 'Education', 'Experiences'];
            var columnsMatch = requiredColumns.every(function (column) {
                return columns.includes(column);
            });

            if (columnsMatch) {
                // Required columns match
                $('#submitbtn').show();
                $('#fakebtn').hide();
            } else {
                // Required columns do not match
                $('.imgupload').hide('slow');
                $('.imgupload.ok').hide('slow');
                $('.imgupload.stop').show('slow');

                $('#namefile').css({ color: 'red', 'font-weight': 700 });
                $('#namefile').html('Invalid file structure! Please make sure the file contains at least the following :');

                $('#submitbtn').hide();
                $('#fakebtn').show();
            }
        };
        reader.readAsText($('#fileup')[0].files[0]);
    }
});