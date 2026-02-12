import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Input,
  Renderer2,
} from '@angular/core';
import {marked} from '../../web/external/marked';
import hljs from 'highlight.js';
import {
  Key,
  Style,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {MarkdownType} from 'mesop/mesop/components/markdown/markdown_jspb_proto_pb/mesop/components/markdown/markdown_pb';
import {formatStyle} from '../../web/src/utils/styles';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-markdown',
  templateUrl: 'markdown.ng.html',
  standalone: true,
})
export class MarkdownComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;

  htmlOutput = '';

  private _codeBlocks: string[] = [];
  private _config!: MarkdownType;

  constructor(
    readonly changeDetectorRef: ChangeDetectorRef,
    private renderer: Renderer2,
    private el: ElementRef,
  ) {}

  async ngOnChanges() {
    this._config = MarkdownType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );

    // Create a custom renderer so we can add highlighting and a copy button to code
    // blocks.
    //
    // We recreate the renderer each time the markdown gets updated, since we need to
    // keep track of the code blocks for the copy button.
    //
    const renderer = new marked.Renderer();
    this._codeBlocks = [];
    // We do not put the raw code in the HTML markup. Instead we just add the index of
    // the raw code to look up on click.
    let index = -1;
    renderer.code = ({text, lang}) => {
      const language = lang !== undefined && hljs.getLanguage(lang) ? lang : '';
      const highlighted =
        language === ''
          ? hljs.highlightAuto(text).value
          : hljs.highlight(language, text, true).value;
      this._codeBlocks.push(text);
      index += 1;
      // We use an "a" tag since the button tag gets filtered out.
      // Also, we use a class tag since data attributes and ids will get filtered out.
      return `<div class="code-block"><a class="code-copy-${index} code-copy"><span role="img" class="mat-icon notranslate material-symbols-rounded mat-icon-no-color code-copy-${index} code-copy" aria-hidden="true" data-mat-icon-type="font">content_copy</span></a><pre><code class="hljs ${language}">${highlighted}</code></pre></div>`;
    };

    // Use the custom renderer in Marked.js
    marked.setOptions({renderer});

    this.htmlOutput = await marked.parse(this._config!.getText()!, {gfm: true});
    this.renderer.listen(this.el.nativeElement, 'click', (e: Event) => {
      const target = e.target as HTMLElement;
      if (target.classList.contains('code-copy')) {
        for (let i = 0; i < target.classList.length; i++) {
          const className = target.classList[i];
          if (className.startsWith('code-copy-')) {
            const parts = className.split('-');
            const index = parseInt(parts[parts.length - 1]);
            navigator.clipboard.writeText(this._codeBlocks[index]);
            break;
          }
        }
      }
    });
  }

  config(): MarkdownType {
    return this._config;
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
