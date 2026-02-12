import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Style,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {LinkType} from 'mesop/mesop/components/link/link_jspb_proto_pb/mesop/components/link/link_pb';
import {formatStyle} from '../../web/src/utils/styles';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-link',
  templateUrl: 'link.ng.html',
  styleUrl: 'link.css',
  standalone: true,
})
export class LinkComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: LinkType;

  ngOnChanges() {
    this._config = LinkType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): LinkType {
    return this._config;
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
