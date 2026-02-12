import {
  CSP_NONCE,
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  Inject,
  Input,
  ViewChild,
} from '@angular/core';
import {
  Key,
  Style,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {HtmlType} from 'mesop/mesop/components/html/html_jspb_proto_pb/mesop/components/html/html_pb';
import {formatStyle} from '../../web/src/utils/styles';
import {setIframeSrc} from '../../web/src/safe_iframe/safe_iframe';
import {prefixBasePath} from '../../web/src/utils/base_path';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-html',
  templateUrl: 'html.ng.html',
  standalone: true,
})
export class HtmlComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  @ViewChild('iframe', {read: ElementRef}) iframe!: ElementRef;
  private _config!: HtmlType;
  isSandboxed!: boolean;
  html!: string;

  constructor(
    private destroyRef: DestroyRef,
    @Inject(CSP_NONCE) private cspNonce: string,
  ) {}

  ngOnChanges() {
    this._config = HtmlType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
    this.isSandboxed = this._config.getMode() === 'sandboxed';
    if (!this.isSandboxed) {
      return;
    }
    const previousHtml = this.html;
    this.html = this._config.getHtml()!;
    // Reload iframe if the HTML has changed.
    if (
      this.html !== previousHtml &&
      this.iframe &&
      this.iframe.nativeElement
    ) {
      this.loadIframe();
    }
  }

  ngAfterViewInit() {
    if (this.isSandboxed) {
      this.loadIframe();
    }
  }

  loadIframe(): void {
    if (!this.iframe) {
      console.warn(
        'iframe element in Mesop html component unexpectedly not found',
      );
      return;
    }

    const iframe = this.iframe.nativeElement as HTMLIFrameElement;
    setIframeSrc(iframe, prefixBasePath('/sandbox_iframe.html'));
    iframe.onload = () => {
      iframe.contentWindow!.postMessage(
        {
          type: 'mesopExecHtml',
          html: this.html,
        },
        window.location.origin,
      );
    };
  }

  config(): HtmlType {
    return this._config;
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
