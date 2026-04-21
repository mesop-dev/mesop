import {
  LitElement,
  html,
} from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

class HotKeys extends LitElement {
  static properties = {
    // Format: {key: String, action: String modifiers: String}
    hotkeys: {type: Object},
    keyPressEvent: {type: String},
    triggeredAction: {type: String},
  };

  render() {
    return html`
      <div @keydown=${this._onKeyDown} @keyup=${this._onKeyUp}>
        <slot></slot>
      </div>
    `;
  }

  _onKeyUp(e) {
    if (!this.keyPressEvent || !this.triggeredAction) {
      return;
    }
    this.dispatchEvent(
      new MesopEvent(this.keyPressEvent, {
        action: this.triggeredAction,
      }),
    );
    // Reset the action so it won't get resent multiple times.
    this.triggeredAction = '';
  }

  _onKeyDown(e) {
    if (!this.keyPressEvent) {
      return;
    }

    for (const hotkey of this.hotkeys) {
      if (
        e.key === hotkey.key &&
        hotkey.modifiers.every((m) => this._isModifierPressed(e, m))
      ) {
        // Prevent default behavior for cases where we want to override browser level
        // commands, such as Cmd+S.
        e.preventDefault();
        // Store the action and wait for key up to send the event.
        // This is mainly to make text input hot key actions more efficient. If the
        // event is on key up, then the on_enter event will trigger first, allowing
        // the input text to be saved. This way we can avoid using the on_input to
        // to store text (though this wouldn't work for text area unfortunately). This
        // is problematic due to the way web components force a full rerender of the
        // child components, which makes on_input unusable in this scenario since
        // it will keep refreshing the child components. It will also lose focus on the
        // text area.
        this.triggeredAction = hotkey.action;
      }
    }
  }

  _isModifierPressed(event, modifierString) {
    const modifierMap = {
      'ctrl': 'ctrlKey',
      'shift': 'shiftKey',
      'alt': 'altKey',
      'meta': 'metaKey',
    };
    const modifierProperty = modifierMap[modifierString.toLowerCase()];
    return modifierProperty ? event[modifierProperty] : false;
  }
}

customElements.define('hotkeys-component', HotKeys);
