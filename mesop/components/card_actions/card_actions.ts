import {MatCardModule} from '@angular/material/card';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {CardActionsType} from 'mesop/mesop/components/card_actions/card_actions_jspb_proto_pb/mesop/components/card_actions/card_actions_pb';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-card-actions',
  templateUrl: 'card_actions.ng.html',
  standalone: true,
  imports: [MatCardModule],
})
export class CardActionsComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  private _config!: CardActionsType;

  ngOnChanges() {
    this._config = CardActionsType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): CardActionsType {
    return this._config;
  }

  getAlign(): 'start' | 'end' {
    return this.config().getAlign() as 'start' | 'end';
  }
}
