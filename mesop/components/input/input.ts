import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  UserEvent,
  Key,
  Type,
  Shortcut,
  Style,
  TextareaShortcutEvent,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {InputType} from 'mesop/mesop/components/input/input_jspb_proto_pb/mesop/components/input/input_pb';
import {Channel} from '../../web/src/services/channel';
import {formatStyle} from '../../web/src/utils/styles';
import {Subject} from 'rxjs';
import {debounceTime} from 'rxjs/operators';
import {CommonModule} from '@angular/common';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  templateUrl: 'input.ng.html',
  standalone: true,
  imports: [MatInputModule, MatFormFieldModule, CommonModule],
})
export class InputComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: InputType;
  private inputSubject = new Subject<Event>();
  private isComposingCount = 1;
  private expectedIsComposingCount = 1;
  constructor(private readonly channel: Channel) {
    this.inputSubject
      .pipe(
        // Setting this to a short duration to avoid having the user trigger another event
        // during this debounce time period:
        // https://github.com/mesop-dev/mesop/issues/171
        debounceTime(150),
      )
      .subscribe((event) => this.onInputDebounced(event));
    // See keyDown event for explanation for why we have a special case for Safari.
    //
    // Chrome's user-agent basically spoofs other browsers and includes Safari, so we
    // need to explicitly look for the absence of it.
    if (
      navigator.userAgent.includes('Safari') &&
      !navigator.userAgent.includes('Chrome')
    ) {
      this.expectedIsComposingCount = 2;
      this.isComposingCount = 2;
    }
  }

  ngOnDestroy(): void {
    this.inputSubject.unsubscribe();
  }

  ngOnChanges() {
    this._config = InputType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): InputType {
    return this._config;
  }

  getStyle(): string {
    return formatStyle(this.style);
  }

  getColor(): 'primary' | 'accent' | 'warn' {
    return this.config().getColor() as 'primary' | 'accent' | 'warn';
  }

  getFloatLabel(): 'always' | 'auto' {
    return this.config().getFloatLabel() as 'always' | 'auto';
  }

  getAppearance(): 'fill' | 'outline' {
    return this.config().getAppearance() as 'fill' | 'outline';
  }

  getSubscriptSizing(): 'fixed' | 'dynamic' {
    return this.config().getSubscriptSizing() as 'fixed' | 'dynamic';
  }

  onInput(event: Event): void {
    this.inputSubject.next(event);
  }

  onInputDebounced(event: Event): void {
    const userEvent = new UserEvent();
    userEvent.setHandlerId(this.config().getOnInputHandlerId()!);
    userEvent.setStringValue((event.target as HTMLInputElement).value);
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }

  onKeyUp(event: Event): void {
    // See onKeyDown event for why need to check this.isComposingCount.
    const keyboardEvent = event as KeyboardEvent;
    if (
      keyboardEvent.key === 'Enter' &&
      this.isComposingCount === this.expectedIsComposingCount
    ) {
      const userEvent = new UserEvent();
      userEvent.setHandlerId(this.config().getOnEnterHandlerId()!);
      userEvent.setStringValue((event.target as HTMLInputElement).value);
      userEvent.setKey(this.key);
      this.channel.dispatch(userEvent);
    }
  }

  onKeyDown(event: Event): void {
    const keyboardEvent = event as KeyboardEvent;
    // The isComposing field tells us if we are using an input method editor (IME) which
    // will display a menu of characters that can't be represented on a standard QWERTY
    // keyboard. The user can select from this menu by pressing "enter" or clicking the
    // menu item. The user will then need to press "enter" to confirm the selection (at
    // least on MacOS).
    //
    // If we do not check isComposing on key up, this will trigger the Mesop on enter
    // event.
    //
    // If we check isComposing on key up, the enter confirmation will trigger the Mesop
    // on enter event since isComposing becomes false on key up.
    //
    // We need to track isComposing with the key down event since this will trigger the
    // on enter event when "enter" is pressed again (when the IME is inactive and
    // a selection has been made and applied).
    //
    // Safari has a bug where the order of operations for isComposing is in a different
    // order. See https://bugs.webkit.org/show_bug.cgi?id=165004.
    //
    // In order to work around this issue, we need to count expectedIsComposingCount
    // equals false twice on Safari rather than just once.
    if (keyboardEvent.isComposing) {
      this.isComposingCount = 0;
    } else if (this.isComposingCount < this.expectedIsComposingCount) {
      this.isComposingCount += 1;
    }

    // Handle keyboard shortcut events (textareas only)
    for (const shortcutHandler of this._config.getOnShortcutHandlerList()) {
      if (
        keyboardEvent.key.toLowerCase() ===
          shortcutHandler.getShortcut()!.getKey()!.toLowerCase() &&
        keyboardEvent.altKey === shortcutHandler.getShortcut()!.getAlt() &&
        keyboardEvent.ctrlKey === shortcutHandler.getShortcut()!.getCtrl() &&
        keyboardEvent.shiftKey === shortcutHandler.getShortcut()!.getShift() &&
        keyboardEvent.metaKey === shortcutHandler.getShortcut()!.getMeta()
      ) {
        // Prevent default behavior for cases where we want to override browser level
        // commands, such as Cmd+S.
        keyboardEvent.preventDefault();

        const userEvent = new UserEvent();
        userEvent.setHandlerId(shortcutHandler.getHandlerId()!);
        const shortcut = new Shortcut();
        shortcut.setKey(shortcutHandler.getShortcut()!.getKey()!);
        shortcut.setAlt(shortcutHandler.getShortcut()!.getAlt()!);
        shortcut.setCtrl(shortcutHandler.getShortcut()!.getCtrl()!);
        shortcut.setShift(shortcutHandler.getShortcut()!.getShift()!);
        shortcut.setMeta(shortcutHandler.getShortcut()!.getMeta()!);
        const shortcutEvent = new TextareaShortcutEvent();
        shortcutEvent.setShortcut(shortcut);
        shortcutEvent.setStringValue((event.target as HTMLInputElement).value);
        userEvent.setTextareaShortcut(shortcutEvent);
        userEvent.setKey(this.key);
        this.channel.dispatch(userEvent);
        break;
      }
    }
  }

  onBlur(event: Event): void {
    const userEvent = new UserEvent();
    userEvent.setHandlerId(this.config().getOnBlurHandlerId()!);
    userEvent.setStringValue((event.target as HTMLInputElement).value);
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }
}
