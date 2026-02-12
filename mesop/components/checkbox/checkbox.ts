import {MatCheckboxModule, MatCheckboxChange} from '@angular/material/checkbox';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  UserEvent,
  Key,
  Type,
  Style,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {CheckboxType} from 'mesop/mesop/components/checkbox/checkbox_jspb_proto_pb/mesop/components/checkbox/checkbox_pb';
import {Channel} from '../../web/src/services/channel';
import {formatStyle} from '../../web/src/utils/styles';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  templateUrl: 'checkbox.ng.html',
  standalone: true,
  imports: [MatCheckboxModule],
})
export class CheckboxComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;

  private _config!: CheckboxType;

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = CheckboxType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): CheckboxType {
    return this._config;
  }

  getLabelPosition(): 'before' | 'after' {
    return this.config().getLabelPosition() as 'before' | 'after';
  }

  onCheckboxChangeEvent(event: MatCheckboxChange): void {
    const userEvent = new UserEvent();
    userEvent.setBoolValue(event.checked);
    userEvent.setHandlerId(this.config().getOnCheckboxChangeEventHandlerId()!);
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }

  onCheckboxIndeterminateChangeEvent(event: boolean): void {
    const userEvent = new UserEvent();
    userEvent.setBoolValue(event);
    userEvent.setHandlerId(
      this.config().getOnCheckboxIndeterminateChangeEventHandlerId()!,
    );
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
