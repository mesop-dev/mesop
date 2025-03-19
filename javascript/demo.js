const urlParams = new URLSearchParams(window.location.search);
const demoParam = urlParams.get('demo') || '';

const iframe = document.createElement('iframe');
iframe.src = 'https://wwwillchen-mesop.hf.space/' + demoParam;
iframe.className = 'full-screen-iframe';
document.body.appendChild(iframe);
