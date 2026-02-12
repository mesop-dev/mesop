import {MatButtonModule} from '@angular/material/button';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  ClickEvent,
  UserEvent,
  Key,
  Type,
  Style,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {ButtonType} from 'mesop/mesop/components/button/button_jspb_proto_pb/mesop/components/button/button_pb';
import {Channel} from '../../web/src/services/channel';
import {formatStyle} from '../../web/src/utils/styles';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  templateUrl: 'button.ng.html',
  standalone: true,
  imports: [MatButtonModule],
})
export class ButtonComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: ButtonType;

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = ButtonType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): ButtonType {
    return this._config;
  }

  onClick(event: MouseEvent): void {
    const userEvent = new UserEvent();
    userEvent.setHandlerId(this.config().getOnClickHandlerId()!);
    userEvent.setKey(this.key);
    const click = new ClickEvent();
    click.setIsTarget(event.target === event.currentTarget);
    click.setClientX(event.clientX);
    click.setClientY(event.clientY);
    click.setPageX(event.pageX);
    click.setPageY(event.pageY);
    click.setOffsetX(event.offsetX);
    click.setOffsetY(event.offsetY);
    userEvent.setClick(click);
    this.channel.dispatch(userEvent);
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
