import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {AudioType} from 'mesop/mesop/components/audio/audio_jspb_proto_pb/mesop/components/audio/audio_pb';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-audio',
  templateUrl: 'audio.ng.html',
  standalone: true,
})
export class AudioComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  private _config!: AudioType;

  ngOnChanges() {
    this._config = AudioType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): AudioType {
    return this._config;
  }
}
