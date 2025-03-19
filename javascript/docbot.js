document.body.setAttribute('tabindex', '-1');

// Function to show the docbot iframe
function showDocbotIframe() {
  const iframe = document.getElementById('docbot-iframe');

  iframe.style.display = 'block';
  console.log('focusIframe');
  iframe.focus();
  iframe.contentWindow.postMessage('focus', '*');

  // Add event listener to close iframe when clicking outside the iframe
  document.addEventListener('click', closeIframe);
}

function closeIframe(e) {
  const iframe = document.getElementById('docbot-iframe');
  if (!iframe.contains(e.target)) {
    closeDocbot();
  }
}
// Listen for click events on the search input
document.addEventListener(
  'click',
  function (event) {
    console.log('event.target', event.target);
    if (event.target.matches('[data-md-toggle="search"]')) {
      event.preventDefault(); // Prevent default search behavior
      event.stopPropagation();
      showDocbotIframe();
    }
    if (event.target.matches('.md-search__input')) {
      event.preventDefault(); // Prevent default search behavior
      event.stopPropagation();
      showDocbotIframe();
    }
  },
  // Added 'true' for event capture so we can intercept before mkdocs material
  // handles the search button clicks.
  true,
);

document.addEventListener(
  'keydown',
  function (event) {
    console.log('keydown', event);
    // Check if the Escape key is pressed
    if (event.key === 'Escape') {
      const iframe = document.getElementById('docbot-iframe');
      if (iframe.style.display === 'block') {
        closeDocbot();
      }
      return;
    }
    // Check if Command (Mac) or Control (Windows) + K is pressed
    if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
      event.preventDefault();
      const iframe = document.getElementById('docbot-iframe');
      if (iframe.style.display === 'block') {
        closeDocbot();
        return;
      }
      showDocbotIframe();
    }
  },
  true,
);

// Create the iframe
function createDocbotIframe() {
  const iframe = document.createElement('iframe');
  iframe.id = 'docbot-iframe';
  iframe.src = ['http://localhost:8000', 'http://127.0.0.1:8000'].includes(
    window.location.origin,
  )
    ? 'http://localhost:32123'
    : 'https://wwwillchen-mesop-docs-bot.hf.space/';
  iframe.style.position = 'fixed';
  iframe.style.display = 'none';
  iframe.style.top = '50%';
  iframe.style.left = '50%';
  iframe.style.transform = 'translate(-50%, -50%)';
  iframe.style.width = '80%';
  iframe.style.maxWidth = '720px';
  iframe.style.maxHeight = '600px';
  iframe.style.height = '80%';
  iframe.style.border = 'none';
  iframe.style.borderRadius = '16px';
  iframe.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
  iframe.style.zIndex = '9999';

  // Append the iframe to the body
  document.body.appendChild(iframe);

  return iframe;
}

createDocbotIframe();

// Listen for 'message' events from the docbot iframe
window.addEventListener('message', function (event) {
  if (event.data === 'closeDocbot') {
    closeDocbot();
  }
});

function closeDocbot() {
  const iframe = document.getElementById('docbot-iframe');
  iframe.style.display = 'none';
  // Put focus back on the body so keyboard shortcuts work
  document.body.focus();

  // This is a hack because the iframe steals focus. I believe
  // it's because we reload the iframe below.
  setTimeout(() => {
    if (document.activeElement === iframe) {
      document.body.focus();
    }
  }, 500);

  // Reload the iframe
  iframe.src = iframe.src;
  document.removeEventListener('click', closeIframe);
}
