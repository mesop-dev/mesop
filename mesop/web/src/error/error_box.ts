import {ChangeDetectionStrategy, Component, Inject, Input} from '@angular/core';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {
  ServerError,
  StackFrame,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';

import {CommonModule} from '@angular/common';
import {Channel} from '../services/channel';
import {marked} from '../../external/marked';
import {MatIconModule} from '@angular/material/icon';
import {MAT_DIALOG_DATA, MatDialogModule} from '@angular/material/dialog';
import {MatButtonModule} from '@angular/material/button';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-error-box',
  templateUrl: 'error_box.ng.html',
  styleUrl: 'error_box.css',
  standalone: true,
  imports: [
    CommonModule,
    MatProgressBarModule,
    MatIconModule,
    MatDialogModule,
    MatButtonModule,
  ],
  providers: [Channel],
})
export class ErrorBox {
  _showFullTraceback = false;
  _lastAppFrame: StackFrame | undefined;
  @Input({required: true}) error!: ServerError;
  markdownHTML = '';

  async ngOnChanges() {
    this.markdownHTML = (
      await marked.parse(this.error.getException()!.trim())
    ).trim();
    const traceback = this.error.getTraceback();
    if (!traceback) {
      return;
    }
    for (const frame of traceback.getFramesList().slice().reverse()) {
      if (frame.getIsAppCode()) {
        this._lastAppFrame = frame;
        return;
      }
    }
  }

  turnOnFullTraceBack() {
    this._showFullTraceback = true;
  }

  showFullTraceback() {
    if (this._showFullTraceback) {
      return true;
    }
    const traceback = this.error.getTraceback();
    if (!traceback) {
      return false;
    }
    return traceback.getFramesList().every((frame) => !frame.getIsAppCode());
  }

  formatFrame(frame: StackFrame): string {
    return `${frame.getFilename()}:${frame.getLineNumber()} | ${frame.getCodeName()}`;
  }

  isLastAppCode(frame: StackFrame): boolean {
    return frame === this._lastAppFrame;
  }
}

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-server-error-dialog',
  template: ` <mesop-error-box [error]="data.error"></mesop-error-box> `,
  styles: `
    :host {
      display: block;
      max-height: 80vh;
      background-color: #ffe5e5;
      overflow: auto;
    }
  `,
  standalone: true,
  imports: [MatDialogModule, MatButtonModule, ErrorBox],
})
export class ServerErrorBoxDialogComponent {
  constructor(@Inject(MAT_DIALOG_DATA) public data: {error: ServerError}) {}
}
