import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  Input,
  ViewChild,
} from '@angular/core';
import {
  Key,
  Style,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {EmbedType} from 'mesop/mesop/components/embed/embed_jspb_proto_pb/mesop/components/embed/embed_pb';
import {formatStyle} from '../../web/src/utils/styles';
import {setIframeSrc} from '../../web/src/safe_iframe/safe_iframe';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-embed',
  templateUrl: 'embed.ng.html',
  standalone: true,
})
export class EmbedComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  @ViewChild('iframe', {read: ElementRef}) iframe!: ElementRef;

  private _config!: EmbedType;
  private srcUrl!: string;

  ngOnChanges() {
    this._config = EmbedType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
    const previousUrl = this.srcUrl;
    this.srcUrl = this._config.getSrc()!;

    // Reload iframe if the URL has changed.
    if (
      this.srcUrl !== previousUrl &&
      this.iframe &&
      this.iframe.nativeElement
    ) {
      this.loadIframe();
    }
  }

  ngAfterViewInit() {
    this.loadIframe();
  }

  loadIframe() {
    setIframeSrc(this.iframe.nativeElement, this.srcUrl);
  }

  config(): EmbedType {
    return this._config;
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
