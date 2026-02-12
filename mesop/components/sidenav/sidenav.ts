import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  UserEvent,
  Key,
  Style,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {SidenavType} from 'mesop/mesop/components/sidenav/sidenav_jspb_proto_pb/mesop/components/sidenav/sidenav_pb';
import {MatSidenavModule} from '@angular/material/sidenav';
import {formatStyle} from '../../web/src/utils/styles';
import {Channel} from '../../web/src/services/channel';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-sidenav',
  templateUrl: 'sidenav.ng.html',
  standalone: true,
  imports: [MatSidenavModule],
})
export class SidenavComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: SidenavType;

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = SidenavType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): SidenavType {
    return this._config;
  }

  getStyle(): string {
    return formatStyle(this.style);
  }

  getPosition(): 'start' | 'end' {
    return this.config().getPosition() as 'start' | 'end';
  }

  onOpenedChange(isOpened: boolean): void {
    const userEvent = new UserEvent();
    userEvent.setHandlerId(this.config().getOnOpenedChangedEventHandlerId()!);
    userEvent.setBoolValue(isOpened);
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }
}
