import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Style,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {TextType} from 'mesop/mesop/components/text/text_jspb_proto_pb/mesop/components/text/text_pb';
import {formatStyle} from '../../web/src/utils/styles';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-text',
  templateUrl: 'text.ng.html',
  standalone: true,
})
export class TextComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  _config!: TextType;

  getClass(): string {
    return `mat-${this.config().getType()}`;
  }

  ngOnChanges() {
    this._config = TextType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): TextType {
    return this._config;
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
