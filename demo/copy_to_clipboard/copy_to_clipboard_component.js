import {
  LitElement,
  html,
} from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

class CopyToClipboard extends LitElement {
  static properties = {
    text: {type: String},
  };

  constructor() {
    super();
    this.text = '';
  }

  render() {
    return html`
      <div @click="${this._onClick}">
        <slot></slot>
      </div>
    `;
  }

  _onClick() {
    navigator.clipboard
      .writeText(this.text)
      .catch((err) => console.error('Failed to copy text: ', err));
  }
}

customElements.define('copy-to-clipboard-component', CopyToClipboard);
