// static/script.js
console.log("Hash Toolbox client script loaded");

// small UX: if user selects a file, clear text input to avoid confusion
document.addEventListener('DOMContentLoaded', function() {
  const fileInput = document.querySelector('input[type="file"][name="file_input"]') ||
                    document.querySelector('input[type="file"]');
  const textArea = document.querySelector('textarea[name="text_input"]');
  if (fileInput && textArea) {
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) {
        textArea.value = '';
      }
    });
  }
});

