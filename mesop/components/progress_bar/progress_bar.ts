import {
  MatProgressBarModule,
  ProgressAnimationEnd,
} from '@angular/material/progress-bar';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  UserEvent,
  Key,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {ProgressBarType} from 'mesop/mesop/components/progress_bar/progress_bar_jspb_proto_pb/mesop/components/progress_bar/progress_bar_pb';
import {Channel} from '../../web/src/services/channel';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  templateUrl: 'progress_bar.ng.html',
  standalone: true,
  imports: [MatProgressBarModule],
})
export class ProgressBarComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  private _config!: ProgressBarType;

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = ProgressBarType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): ProgressBarType {
    return this._config;
  }

  getMode(): 'determinate' | 'indeterminate' | 'buffer' | 'query' {
    return this.config().getMode() as
      | 'determinate'
      | 'indeterminate'
      | 'buffer'
      | 'query';
  }

  onProgressBarAnimationEndEvent(event: ProgressAnimationEnd): void {
    const userEvent = new UserEvent();
    userEvent.setDoubleValue(event.value);
    userEvent.setHandlerId(
      this.config().getOnProgressBarAnimationEndEventHandlerId()!,
    );
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }
}
