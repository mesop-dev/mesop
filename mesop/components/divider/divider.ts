import {MatDividerModule} from '@angular/material/divider';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {DividerType} from 'mesop/mesop/components/divider/divider_jspb_proto_pb/mesop/components/divider/divider_pb';
import {Channel} from '../../web/src/services/channel';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  templateUrl: 'divider.ng.html',
  standalone: true,
  imports: [MatDividerModule],
})
export class DividerComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  private _config!: DividerType;

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = DividerType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): DividerType {
    return this._config;
  }
}
