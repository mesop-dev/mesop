import {MatCardModule} from '@angular/material/card';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {CardContentType} from 'mesop/mesop/components/card_content/card_content_jspb_proto_pb/mesop/components/card_content/card_content_pb';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-card-content',
  templateUrl: 'card_content.ng.html',
  standalone: true,
  imports: [MatCardModule],
})
export class CardContentComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  private _config!: CardContentType;

  ngOnChanges() {
    this._config = CardContentType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): CardContentType {
    return this._config;
  }
}
