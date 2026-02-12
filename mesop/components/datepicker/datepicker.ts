import {
  MatDatepickerModule,
  MatDatepickerInputEvent,
} from '@angular/material/datepicker';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {
  UserEvent,
  Key,
  Type,
  Style,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {DatePickerType} from 'mesop/mesop/components/datepicker/datepicker_jspb_proto_pb/mesop/components/datepicker/datepicker_pb';
import {CommonModule} from '@angular/common';
import {Channel} from '../../web/src/services/channel';
import {formatStyle} from '../../web/src/utils/styles';
import {provideNativeDateAdapter} from '@angular/material/core';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-datepicker',
  templateUrl: 'datepicker.ng.html',
  standalone: true,
  providers: [provideNativeDateAdapter()],
  imports: [
    MatDatepickerModule,
    MatFormFieldModule,
    MatInputModule,
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
  ],
})
export class DatepickerComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: DatePickerType;

  readonly date = new FormControl();
  private initialDate = '';

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = DatePickerType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );

    const initialDate = this._config.getValue() || '';
    if (this.initialDate !== initialDate) {
      this.initialDate = initialDate;
      this.date.setValue(this.makeDate(initialDate));
    }
  }

  onChange(event: MatDatepickerInputEvent<Date>): void {
    if (this.date.value) {
      const userEvent = new UserEvent();
      userEvent.setHandlerId(this.config().getOnChangeHandlerId()!);
      userEvent.setStringValue(this.makeDateString(this.date.value));
      userEvent.setKey(this.key);
      this.channel.dispatch(userEvent);
    }
  }

  private makeDate(dateInput: string): Date | null {
    if (dateInput) {
      const [year, month, date] = dateInput.split('-').map((e) => parseInt(e));
      return new Date(year, month - 1, date);
    }
    return null;
  }

  private makeDateString(date: Date | null): string {
    return date
      ? `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`
      : '';
  }

  config(): DatePickerType {
    return this._config;
  }

  getStyle(): string {
    return formatStyle(this.style);
  }

  getColor(): 'primary' | 'accent' | 'warn' {
    return this.config().getColor() as 'primary' | 'accent' | 'warn';
  }

  getFloatLabel(): 'always' | 'auto' {
    return this.config().getFloatLabel() as 'always' | 'auto';
  }

  getAppearance(): 'fill' | 'outline' {
    return this.config().getAppearance() as 'fill' | 'outline';
  }

  getSubscriptSizing(): 'fixed' | 'dynamic' {
    return this.config().getSubscriptSizing() as 'fixed' | 'dynamic';
  }
}
