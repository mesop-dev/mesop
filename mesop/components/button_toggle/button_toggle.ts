import {
  MatButtonToggleModule,
  MatButtonToggleChange,
} from '@angular/material/button-toggle';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Type,
  Style,
  UserEvent,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {
  ButtonToggleType,
  ButtonToggleChangeEvent,
} from 'mesop/mesop/components/button_toggle/button_toggle_jspb_proto_pb/mesop/components/button_toggle/button_toggle_pb';
import {Channel} from '../../web/src/services/channel';
import {formatStyle} from '../../web/src/utils/styles';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-button-toggle',
  templateUrl: 'button_toggle.ng.html',
  standalone: true,
  imports: [MatButtonToggleModule],
})
export class ButtonToggleComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: ButtonToggleType;

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = ButtonToggleType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): ButtonToggleType {
    return this._config;
  }

  onChangeEvent(event: MatButtonToggleChange): void {
    const userEvent = new UserEvent();
    userEvent.setHandlerId(this.config().getOnChangeEventHandlerId()!);
    const changeEvent = new ButtonToggleChangeEvent();
    if (typeof event.value === 'string') {
      changeEvent.addValues(event.value);
    } else {
      for (const value of event.value) {
        changeEvent.addValues(value);
      }
    }
    userEvent.setBytesValue(changeEvent.serializeBinary());
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }

  isChecked(value: string): boolean {
    return this.config().getValueList().includes(value);
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
