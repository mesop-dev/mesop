import {MatButtonModule} from '@angular/material/button';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Type,
  UserEvent,
  Style,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {
  UploaderType,
  UploadEvent,
  UploadedFile,
} from 'mesop/mesop/components/uploader/uploader_jspb_proto_pb/mesop/components/uploader/uploader_pb';
import {Channel} from '../../web/src/services/channel';
import {formatStyle} from '../../web/src/utils/styles';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-uploader',
  styleUrl: 'uploader.css',
  templateUrl: 'uploader.ng.html',
  standalone: true,
  imports: [MatButtonModule],
})
export class UploaderComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: UploaderType;

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = UploaderType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): UploaderType {
    return this._config;
  }

  accept(): string {
    // For accepted file list into the format specified at
    // https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/file#accept
    return this._config.getAcceptedFileTypeList().join(',');
  }

  async onFileSelected(event: Event) {
    const target = event.target as HTMLInputElement;
    const files = target.files as FileList;
    const uploadEvent = new UploadEvent();

    for (let i = 0; i < files.length; ++i) {
      const uploaded_file = new UploadedFile();
      const buffer = await files[i].arrayBuffer();
      uploaded_file.setName(files[i].name);
      uploaded_file.setSize(files[i].size);
      uploaded_file.setMimeType(files[i].type);
      uploaded_file.setContents(new Uint8Array(buffer));
      uploadEvent.addFile(uploaded_file);
    }

    const userEvent = new UserEvent();
    userEvent.setHandlerId(this.config().getOnUploadEventHandlerId()!);
    userEvent.setKey(this.key);
    userEvent.setBytesValue(uploadEvent.serializeBinary());
    this.channel.dispatch(userEvent);

    // Reset the uploaded file, so that the same file path can be reselected.
    target.value = '';
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
