import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Style,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {ImageType} from 'mesop/mesop/components/image/image_jspb_proto_pb/mesop/components/image/image_pb';
import {formatStyle} from '../../web/src/utils/styles';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-image',
  templateUrl: 'image.ng.html',
  standalone: true,
})
export class ImageComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: ImageType;

  ngOnChanges() {
    this._config = ImageType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): ImageType {
    return this._config;
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
