// myreportapp/static/js/


function fakePlacehold(element, str_value) {
    element.value = str_value;
    element.blur();
    element.addEventListener('focus', function () {
        if (element.value === str_value) {
            element.value = '';
        }
    });

    element.addEventListener('blur', function () {
        if (element.value === '') {
            element.value = str_value;
        }
    });
    element.blur();
}

function toNiceName(someOneName) {
    const prepositions = new Set(['de', 'da', 'do', 'dos', 'das', 'e', 'ou', 'para', 'com', 'em', 'a', 'o', 'do', 'dos']);
    const treatmentTerms = new Set(['PM', 'GCM', 'GM', 'PMR', 'EPC']); // Termos de tratamento que devem ser exibidos em maiúsculas
    const words = someOneName.split(/\s+/);
    const formatedWords = words.map((word, index) => {
        const lowerCaseWord = word.toLowerCase();
        const upperCaseWord = word.toUpperCase();
        if (treatmentTerms.has(upperCaseWord)) {
            return upperCaseWord; // Termos de tratamento sempre em maiúsculas
        } else if (prepositions.has(lowerCaseWord) && index !== 0 && index !== words.length - 1) {
            return lowerCaseWord; // Preposições em minúsculas (exceto se for a primeira ou última palavra)
        } else {
            return lowerCaseWord.charAt(0).toUpperCase() + lowerCaseWord.slice(1); // Primeira letra maiúscula para outros casos
        }
    });
    return formatedWords.join(' ');
}

function adjustProtocol(someString, someDate) {
    if (!isNaN(someString)) {
        someString = someString.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    }
    if (/[a-zA-Z]/.test(someString)) {
        someString = someString.toUpperCase();
    }
    if (someString.includes('/')) {
        return someString;
    }
    const dateObject = new Date(someDate);
    if (isNaN(dateObject.getTime())) {
        throw new Error("Data inválida fornecida.");
    }
    const year = dateObject.getFullYear();
    return `${someString}/${year}`;
}


function validDate(someValue) {
    if (!someValue) return false;
    let isoFormat = /^\d{4}-\d{2}-\d{2}$/;
    let brFormat = /^\d{2}\/\d{2}\/\d{4}$/;
    if (isoFormat.test(someValue)) {
        let date = new Date(someValue);
        return !isNaN(date.getTime());
    }     
    if (brFormat.test(someValue)) {
        let [day, month, year] = someValue.split('/').map(Number);
        let date = new Date(year, month - 1, day);
        return date.getFullYear() === year && (date.getMonth() + 1) === month && date.getDate() === day;
    }
    return false;
}

function validHour(someTime) {
    if (!someTime) return false;
    let timeFormat = /^([01]\d|2[0-3]):([0-5]\d)$/;
    if (timeFormat.test(someTime)) {
        let [hours, minutes] = someTime.split(":").map(Number);
        return hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59;
    }
    return false;
}


