/* path: myreport/report_maker/static/report_maker/js/markdown_editor.js */
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

    textarea.value = value.slice(0, start) + replacement + value.slice(end);

    textarea.focus();
    textarea.selectionStart = start + before.length;
    textarea.selectionEnd = start + before.length + selected.length;
  }

  function insertAtCursor(textarea, text) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const value = textarea.value;

    textarea.value = value.slice(0, start) + text + value.slice(end);

    textarea.focus();
    textarea.selectionStart = start + text.length;
    textarea.selectionEnd = start + text.length;
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
        wrapSelection(textarea, "$", "$");
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
        break;
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