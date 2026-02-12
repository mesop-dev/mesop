import {
  ChangeDetectionStrategy,
  Component,
  Inject,
  Injectable,
} from '@angular/core';
import {MatButtonModule} from '@angular/material/button';
import {
  MAT_DIALOG_DATA,
  MatDialog,
  MatDialogModule,
} from '@angular/material/dialog';

export abstract class ErrorDialogService {
  abstract showError(error: any): void;
}

export class ProdErrorDialogService implements ErrorDialogService {
  showError(error: any): void {
    console.error(error);
  }
}

@Injectable()
export class DebugErrorDialogService implements ErrorDialogService {
  constructor(private dialog: MatDialog) {}

  showError(error: any): void {
    console.error(error);
    this.dialog.open(ErrorDialogComponent, {
      width: '400px',
      data: {error: error},
    });
  }
}

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-error-dialog',
  template: `
    <h3 mat-dialog-title>Mesop Error</h3>
    <mat-dialog-content class="mat-typography">
      <div class="error-content">{{ data.error }}</div>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button color="warn" [mat-dialog-close]="true" cdkFocusInitial>
        OK
      </button>
    </mat-dialog-actions>
  `,
  styles: `
    :host {
      display: block;
      background: var(--sys-error-container);
      --mdc-dialog-supporting-text-size: 16px;
      --mdc-dialog-supporting-text-line-height: 1.5;
    }

    .error-content {
      white-space: break-spaces;
    }
  `,
  standalone: true,
  imports: [MatDialogModule, MatButtonModule],
})
export class ErrorDialogComponent {
  constructor(@Inject(MAT_DIALOG_DATA) public data: {error: Error}) {}
}
