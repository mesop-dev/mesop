import {MatCardModule} from '@angular/material/card';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Type,
  Style,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {CardType} from 'mesop/mesop/components/card/card_jspb_proto_pb/mesop/components/card/card_pb';
import {formatStyle} from '../../web/src/utils/styles';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-card',
  templateUrl: 'card.ng.html',
  standalone: true,
  imports: [MatCardModule],
})
export class CardComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: CardType;

  ngOnChanges() {
    this._config = CardType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): CardType {
    return this._config;
  }

  getStyle(): string {
    return formatStyle(this.style);
  }

  getAppearance(): 'outlined' | 'raised' {
    return this.config().getAppearance() as 'outlined' | 'raised';
  }
}
