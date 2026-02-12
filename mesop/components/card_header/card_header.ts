import {MatCardModule} from '@angular/material/card';
import {CommonModule} from '@angular/common';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {CardHeaderType} from 'mesop/mesop/components/card_header/card_header_jspb_proto_pb/mesop/components/card_header/card_header_pb';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-card-header',
  templateUrl: 'card_header.ng.html',
  standalone: true,
  imports: [MatCardModule, CommonModule],
})
export class CardHeaderComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  private _config!: CardHeaderType;

  ngOnChanges() {
    this._config = CardHeaderType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): CardHeaderType {
    return this._config;
  }
}
