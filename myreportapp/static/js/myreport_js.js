// myreportapp/static/js/


function fakePlacehold(element, str_value) {
    element.value = str_value;
    element.blur();
    element.addEventListener('focus', function() {
        if (element.value === str_value) {
            element.value = '';
        }
    });

    element.addEventListener('blur', function() {
        if (element.value === '') {
            element.value = str_value;
        }
    });
    element.blur();
}