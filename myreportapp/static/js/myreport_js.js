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
    const treatmentTerms = new Set(['PM', 'GCM', 'GM', 'PMR']); // Termos de tratamento que devem ser exibidos em maiúsculas
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

