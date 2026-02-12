import {MatRadioModule, MatRadioChange} from '@angular/material/radio';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  UserEvent,
  Key,
  Type,
  Style,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {RadioType} from 'mesop/mesop/components/radio/radio_jspb_proto_pb/mesop/components/radio/radio_pb';
import {Channel} from '../../web/src/services/channel';
import {formatStyle} from '../../web/src/utils/styles';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  templateUrl: 'radio.ng.html',
  styleUrl: 'radio.css',
  standalone: true,
  imports: [MatRadioModule],
})
export class RadioComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: RadioType;

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = RadioType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): RadioType {
    return this._config;
  }

  getColor(): 'primary' | 'accent' | 'warn' {
    return this.config().getColor() as 'primary' | 'accent' | 'warn';
  }

  getLabelPosition(): 'before' | 'after' {
    return this.config().getLabelPosition() as 'before' | 'after';
  }

  onRadioChangeEvent(event: MatRadioChange): void {
    const userEvent = new UserEvent();
    userEvent.setHandlerId(this.config().getOnRadioChangeEventHandlerId()!);
    userEvent.setStringValue(event.value);
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
