/* myreport/report_maker/static/report_maker/js/markdown_editor.js */
(function () {
  "use strict";

  function getEditorContainer(element) {
    return element.closest(".text-block-editor");
  }

  function getTextarea(container) {
    return container.querySelector("textarea");
  }

  function wrapSelection(textarea, before, after) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const value = textarea.value;

    const selected = value.slice(start, end);
    const replacement = `${before}${selected}${after}`;

    textarea.value =
      value.slice(0, start) + replacement + value.slice(end);

    textarea.focus();
    textarea.selectionStart = start + before.length;
    textarea.selectionEnd = start + before.length + selected.length;
  }

  function insertAtCursor(textarea, text) {
    const start = textarea.selectionStart;
    const value = textarea.value;

    textarea.value =
      value.slice(0, start) + text + value.slice(start);

    textarea.focus();
    textarea.selectionStart = textarea.selectionEnd =
      start + text.length;
  }

  function insertMathInline(textarea) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const value = textarea.value;
    const selected = value.slice(start, end);

    if (selected) {
      wrapSelection(textarea, "$", "$");
      return;
    }

    const placeholder = "\\alpha";
    const replacement = `$${placeholder}$`;

    textarea.value =
      value.slice(0, start) + replacement + value.slice(end);

    textarea.focus();
    textarea.selectionStart = start + 1;
    textarea.selectionEnd = start + 1 + placeholder.length;
  }

  function insertMathBlock(textarea) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const value = textarea.value;
    const selected = value.slice(start, end);

    if (selected) {
      const replacement = `\n$$\n${selected}\n$$\n`;

      textarea.value =
        value.slice(0, start) + replacement + value.slice(end);

      textarea.focus();
      textarea.selectionStart = start + 4;
      textarea.selectionEnd = start + 4 + selected.length;
      return;
    }

    const placeholder = "x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}";
    const replacement = `\n$$\n${placeholder}\n$$\n`;

    textarea.value =
      value.slice(0, start) + replacement + value.slice(end);

    textarea.focus();
    textarea.selectionStart = start + 4;
    textarea.selectionEnd = start + 4 + placeholder.length;
  }

  function handleAction(action, textarea) {
    switch (action) {
      case "bold":
        wrapSelection(textarea, "**", "**");
        break;

      case "italic":
        wrapSelection(textarea, "*", "*");
        break;

      case "strike":
        wrapSelection(textarea, "~~", "~~");
        break;

      case "math":
        insertMathInline(textarea);
        break;

      case "math-block":
        insertMathBlock(textarea);
        break;

      case "h2":
        insertAtCursor(textarea, "\n## ");
        break;

      case "quote":
        insertAtCursor(textarea, "\n> ");
        break;

      case "code":
        wrapSelection(textarea, "`", "`");
        break;

      case "ul":
        insertAtCursor(textarea, "\n- ");
        break;

      case "ol":
        insertAtCursor(textarea, "\n1. ");
        break;

      case "hr":
        insertAtCursor(textarea, "\n\n---\n\n");
        break;

      default:
        console.warn("Markdown action desconhecida:", action);
    }
  }

  document.addEventListener("click", function (event) {
    const button = event.target.closest("[data-md]");
    if (!button) return;

    const action = button.dataset.md;
    const container = getEditorContainer(button);
    if (!container) return;

    const textarea = getTextarea(container);
    if (!textarea) return;

    event.preventDefault();
    handleAction(action, textarea);
  });
})();