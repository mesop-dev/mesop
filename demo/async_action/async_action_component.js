import {
  LitElement,
  html,
} from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

class AsyncAction extends LitElement {
  static properties = {
    startedEvent: {type: String},
    finishedEvent: {type: String},
    // Format: {action: String, duration_seconds: Number}
    action: {type: Object},
    isRunning: {type: Boolean},
  };

  render() {
    return html`<div></div>`;
  }

  firstUpdated() {
    if (this.action) {
      this.runTimeout(this.action);
    }
  }

  updated(changedProperties) {
    if (changedProperties.has('action') && this.action) {
      this.runTimeout(this.action);
    }
  }

  runTimeout(action) {
    this.dispatchEvent(
      new MesopEvent(this.startedEvent, {
        action: action,
      }),
    );
    setTimeout(() => {
      this.dispatchEvent(
        new MesopEvent(this.finishedEvent, {
          action: action.value,
        }),
      );
    }, action.duration_seconds * 1000);
  }
}

customElements.define('async-action-component', AsyncAction);
