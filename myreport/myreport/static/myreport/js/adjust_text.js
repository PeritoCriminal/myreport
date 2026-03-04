// myreport/static/myreport/js/adjust_text.js

/**
 * -------------------------------------------------------------------------
 * adjust_text.js
 * -------------------------------------------------------------------------
 * Módulo utilitário responsável por ajustes e padronizações textuais
 * aplicadas no frontend do projeto.
 *
 * Finalidade:
 * - Uniformizar grafia de nomes próprios;
 * - Padronizar protocolos e identificadores numéricos;
 * - Reduzir inconsistências de capitalização;
 * - Evitar variações indesejadas de caixa (maiúsculas/minúsculas).
 *
 * Observação:
 * Este arquivo poderá ser ampliado futuramente para contemplar novas
 * regras de normalização textual, conforme a evolução das necessidades
 * do sistema.
 * -------------------------------------------------------------------------
 */


/**
 * Converte um nome para formato padronizado ("Nice Name").
 *
 * Regras aplicadas:
 * - Mantém termos institucionais previamente definidos em caixa alta;
 * - Mantém preposições em caixa baixa quando não estiverem no início
 *   ou no final da expressão;
 * - Aplica capitalização inicial nas demais palavras.
 *
 * @param {string} someOneName - Nome a ser ajustado.
 * @returns {string} Nome formatado conforme regras estabelecidas.
 */
function toNiceName(someOneName) {
  const prepositions = new Set([
    'de', 'da', 'do', 'dos', 'das',
    'e', 'ou', 'para', 'com', 'em',
    'a', 'o'
  ]);

  const treatmentTerms = new Set([
    'PM', 'GCM', 'GM', 'PMR',
    'EPC', 'DP', 'DIG', 'DISE'
  ]);

  const words = someOneName.split(/\s+/);

  return words.map((word, index) => {
    const lower = word.toLowerCase();
    const upper = word.toUpperCase();

    // Mantém siglas institucionais em caixa alta
    if (treatmentTerms.has(upper)) return upper;

    // Mantém preposições internas em caixa baixa
    if (prepositions.has(lower) && index !== 0 && index !== words.length - 1) {
      return lower;
    }

    // Capitaliza demais termos
    return lower.charAt(0).toUpperCase() + lower.slice(1);

  }).join(' ');
}


/**
 * Ajusta e padroniza identificadores de protocolo.
 *
 * Regras aplicadas:
 * - Se a string já contiver "/", apenas converte para caixa alta;
 * - Se for numérica pura, aplica separação de milhar com ponto;
 * - Caso contrário, converte para caixa alta;
 * - Acrescenta automaticamente o ano corrente (ou ano fornecido).
 *
 * @param {string} someString - Identificador a ser ajustado.
 * @param {Date} someDate - Data base para obtenção do ano (opcional).
 * @returns {string} Protocolo formatado.
 */
function adjustProtocol(someString, someDate = new Date()) {

  if (typeof someString !== "string" || someString.trim() === "") {
    return someString;
  }

  someString = someString.trim();

  // Garante que someDate seja um objeto Date válido
  if (!(someDate instanceof Date) || isNaN(someDate)) {
    someDate = new Date();
  }

  // Caso já possua ano informado
  if (someString.includes("/")) {
    return someString.toUpperCase();
  }

  // Se for numérico puro, aplica separador de milhar
  if (/^\d+$/.test(someString)) {
    someString = someString.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  } else {
    someString = someString.toUpperCase();
  }

  const year = someDate.getFullYear();
  return `${someString}/${year}`;
}


/**
 * Função auxiliar para verificação de carregamento do módulo.
 * Destina-se exclusivamente a testes locais.
 */
function teste(){
  alert('Arquivo adjust_text rodando');
}