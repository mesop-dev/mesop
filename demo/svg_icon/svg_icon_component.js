import {
  LitElement,
  html,
} from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export class SVGIconComponent extends LitElement {
  static properties = {
    svg: {type: String},
  };

  render() {
    const span = document.createElement('span');
    span.innerHTML = this.svg;
    return html`${span}`;
  }
}

customElements.define('svg-icon', SVGIconComponent);
