import {MatTooltipModule} from '@angular/material/tooltip';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {TooltipType} from 'mesop/mesop/components/tooltip/tooltip_jspb_proto_pb/mesop/components/tooltip/tooltip_pb';
import {Channel} from '../../web/src/services/channel';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  templateUrl: 'tooltip.ng.html',
  standalone: true,
  imports: [MatTooltipModule],
})
export class TooltipComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  private _config!: TooltipType;

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = TooltipType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): TooltipType {
    return this._config;
  }

  getPosition(): 'left' | 'right' | 'above' | 'below' | 'before' | 'after' {
    return this.config().getPosition() as
      | 'left'
      | 'right'
      | 'above'
      | 'below'
      | 'before'
      | 'after';
  }
}
