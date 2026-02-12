import {
  MatDatepickerModule,
  MatDatepickerInputEvent,
  DateRange,
} from '@angular/material/datepicker';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  FormControl,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
} from '@angular/forms';
import {
  DateRangePickerEvent,
  UserEvent,
  Key,
  Type,
  Style,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {DateRangePickerType} from 'mesop/mesop/components/date_range_picker/date_range_picker_jspb_proto_pb/mesop/components/date_range_picker/date_range_picker_pb';
import {CommonModule} from '@angular/common';
import {Channel} from '../../web/src/services/channel';
import {formatStyle} from '../../web/src/utils/styles';
import {provideNativeDateAdapter} from '@angular/material/core';
import {debounceTime} from 'rxjs/operators';
import {Subject} from 'rxjs';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-date-range-picker',
  templateUrl: 'date_range_picker.ng.html',
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
export class DateRangePickerComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: DateRangePickerType;

  readonly dateRange = new FormGroup({
    start: new FormControl(),
    end: new FormControl(),
  });
  private initialStartDate = '';
  private initialEndDate = '';
  private dateRangeChangeSubject = new Subject<
    MatDatepickerInputEvent<string | undefined, DateRange<string | undefined>>
  >();

  constructor(private readonly channel: Channel) {
    this.dateRangeChangeSubject
      .pipe(debounceTime(30))
      .subscribe((event) => this.onChangeDebounced(event));
  }

  ngOnChanges() {
    this._config = DateRangePickerType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );

    const startDateString = this._config.getStartDate() || '';
    const endDateString = this._config.getEndDate() || '';

    let dateInputUpdated = false;
    if (this.initialStartDate !== startDateString) {
      this.initialStartDate = startDateString;
      dateInputUpdated = true;
    }
    if (this.initialEndDate !== endDateString) {
      this.initialEndDate = endDateString;
      this.initialEndDate = endDateString;
      dateInputUpdated = true;
    }

    if (dateInputUpdated) {
      this.dateRange.setValue({
        start: this.makeDate(startDateString),
        end: this.makeDate(endDateString),
      });
    }
  }

  onChange(
    event: MatDatepickerInputEvent<
      string | undefined,
      DateRange<string | undefined>
    >,
  ): void {
    this.dateRangeChangeSubject.next(event);
  }

  // We debounce the date range change event to avoid an issue where two change events
  // are fired consecutively when resetting the date range.
  //
  // If we send both events, this can cause issues if the value parameters are set on
  // the component. What will happen is the end date will not get reset, which is why
  // we only want to send the second event.
  //
  // The other reason we need debounce is to handle the case where the user edits the
  // start date directly. On blur, only one event will fire. And we need to send this
  // event if the end date is also set.
  onChangeDebounced(
    event: MatDatepickerInputEvent<
      string | undefined,
      DateRange<string | undefined>
    >,
  ): void {
    if (this.dateRange.value.start && this.dateRange.value.end) {
      const userEvent = new UserEvent();
      userEvent.setHandlerId(this.config().getOnChangeHandlerId()!);
      const dateRangeEvent = new DateRangePickerEvent();
      dateRangeEvent.setStartDate(
        this.makeDateString(this.dateRange.value.start),
      );
      dateRangeEvent.setEndDate(this.makeDateString(this.dateRange.value.end));
      userEvent.setDateRangePickerEvent(dateRangeEvent);
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

  config(): DateRangePickerType {
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
