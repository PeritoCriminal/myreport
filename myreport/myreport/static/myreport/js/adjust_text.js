function toNiceName(someOneName) {
  const prepositions = new Set(['de', 'da', 'do', 'dos', 'das', 'e', 'ou', 'para', 'com', 'em', 'a', 'o']);
  const treatmentTerms = new Set(['PM', 'GCM', 'GM', 'PMR', 'EPC', 'DP', 'DIG', 'DISE']);
  const words = someOneName.split(/\s+/);
  return words.map((word, index) => {
    const lower = word.toLowerCase();
    const upper = word.toUpperCase();
    if (treatmentTerms.has(upper)) return upper;
    if (prepositions.has(lower) && index !== 0 && index !== words.length - 1) return lower;
    return lower.charAt(0).toUpperCase() + lower.slice(1);
  }).join(' ');
}

function adjustProtocol(someString, someDate = new Date()) {
  if (typeof someString !== "string" || someString.trim() === "") return someString;

  someString = someString.trim();

  // Se someDate não for um Date válido, corrige:
  if (!(someDate instanceof Date) || isNaN(someDate)) {
    someDate = new Date();
  }

  if (someString.includes("/")) {
    return someString.toUpperCase(); // já contém "/", apenas padroniza para maiúsculo
  }

  if (/^\d+$/.test(someString)) {
    someString = someString.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  } else {
    someString = someString.toUpperCase();
  }

  const year = someDate.getFullYear();
  return `${someString}/${year}`;
}

function teste(){
  alert('Arquivo adjust_text rodando');
}
