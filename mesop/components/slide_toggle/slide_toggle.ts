import {
  MatSlideToggleModule,
  MatSlideToggleChange,
} from '@angular/material/slide-toggle';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  UserEvent,
  Key,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {SlideToggleType} from 'mesop/mesop/components/slide_toggle/slide_toggle_jspb_proto_pb/mesop/components/slide_toggle/slide_toggle_pb';
import {Channel} from '../../web/src/services/channel';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  templateUrl: 'slide_toggle.ng.html',
  standalone: true,
  imports: [MatSlideToggleModule],
})
export class SlideToggleComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  private _config!: SlideToggleType;

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = SlideToggleType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): SlideToggleType {
    return this._config;
  }

  getLabelPosition(): 'before' | 'after' {
    return this.config().getLabelPosition() as 'before' | 'after';
  }

  onSlideToggleChangeEvent(event: MatSlideToggleChange): void {
    const userEvent = new UserEvent();

    userEvent.setHandlerId(
      this.config().getOnSlideToggleChangeEventHandlerId()!,
    );
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }
}
