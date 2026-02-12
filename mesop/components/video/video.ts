import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Style,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {VideoType} from 'mesop/mesop/components/video/video_jspb_proto_pb/mesop/components/video/video_pb';
import {formatStyle} from '../../web/src/utils/styles';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-video',
  templateUrl: 'video.ng.html',
  standalone: true,
})
export class VideoComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: VideoType;

  ngOnChanges() {
    this._config = VideoType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): VideoType {
    return this._config;
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
