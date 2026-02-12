import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {ChangeDetectionStrategy, Component, Input, OnInit} from '@angular/core';
import {
  Key,
  Type,
  UserEvent,
  Style,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {
  AutocompleteType,
  AutocompleteOptionSet,
  AutocompleteOptionGroup,
} from 'mesop/mesop/components/autocomplete/autocomplete_jspb_proto_pb/mesop/components/autocomplete/autocomplete_pb';
import {Channel} from '../../web/src/services/channel';
import {formatStyle} from '../../web/src/utils/styles';
import {Subject} from 'rxjs';
import {debounceTime, startWith} from 'rxjs/operators';
import {AsyncPipe, CommonModule} from '@angular/common';
import {Observable} from 'rxjs';
import {map} from 'rxjs/operators';
import {FormControl, ReactiveFormsModule} from '@angular/forms';
import {
  MatAutocompleteModule,
  MatAutocompleteSelectedEvent,
} from '@angular/material/autocomplete';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-autocomplete',
  templateUrl: 'autocomplete.ng.html',
  standalone: true,
  imports: [
    MatInputModule,
    MatFormFieldModule,
    CommonModule,
    MatAutocompleteModule,
    ReactiveFormsModule,
    AsyncPipe,
  ],
})
export class AutocompleteComponent implements OnInit {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: AutocompleteType;
  private _lastValue = '';
  filteredOptions: Observable<readonly AutocompleteOptionSet[]> =
    new Observable<readonly AutocompleteOptionSet[]>();
  private inputSubject = new Subject<Event>();
  autocompleteControl = new FormControl('');
  constructor(private readonly channel: Channel) {
    this.inputSubject
      .pipe(
        // Setting this to a short duration to avoid having the user trigger another event
        // during this debounce time period:
        // https://github.com/mesop-dev/mesop/issues/171
        debounceTime(150),
      )
      .subscribe((event) => this.onInputDebounced(event));
  }

  ngOnInit(): void {
    this.filteredOptions = this.autocompleteControl.valueChanges.pipe(
      startWith(''),
      map((value) => {
        return this._filter(value || '', this._config.getOptionsList());
      }),
    );
  }

  ngOnDestroy(): void {
    this.inputSubject.unsubscribe();
  }

  ngOnChanges() {
    this._config = AutocompleteType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
    // Set the autocomplete value. But only update if the "initial" value changes.
    if (this._config.getValue()! !== this._lastValue) {
      this._lastValue = this._config.getValue()!;
      this.autocompleteControl.setValue(this._lastValue);
    }
  }

  config(): AutocompleteType {
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

  onInput(event: Event): void {
    this.inputSubject.next(event);
  }

  onInputDebounced(event: Event): void {
    const userEvent = new UserEvent();
    userEvent.setHandlerId(this.config().getOnInputHandlerId()!);
    userEvent.setStringValue((event.target as HTMLInputElement).value);
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }

  onKeyUp(event: Event): void {
    const keyboardEvent = event as KeyboardEvent;
    if (keyboardEvent.key === 'Enter') {
      const userEvent = new UserEvent();
      userEvent.setHandlerId(this.config().getOnEnterHandlerId()!);
      userEvent.setStringValue(this.autocompleteControl.value || '');
      userEvent.setKey(this.key);
      this.channel.dispatch(userEvent);
    }
  }

  onAutocompleteSelectEvent(event: MatAutocompleteSelectedEvent): void {
    const userEvent = new UserEvent();
    userEvent.setHandlerId(this.config().getOnSelectionChangeHandlerId()!);
    userEvent.setStringValue(this.autocompleteControl.value || '');
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }

  /**
   * Filters the autocomplete options based on the current input.
   *
   * The filtering will perform a case-insensitive substring match against the
   * options labels.
   *
   * @param value Value of the input
   * @param options Autocomplete options
   * @returns
   */
  private _filter(
    value: string,
    options: readonly AutocompleteOptionSet[],
  ): readonly AutocompleteOptionSet[] {
    if (!value) {
      return options;
    }
    const filterValue = value.toLowerCase();
    const filteredOptions = new Array<AutocompleteOptionSet>();
    for (const option of options) {
      if (option.getOptionGroup()) {
        const filteredOptionGroup = new AutocompleteOptionGroup();
        filteredOptionGroup.setLabel(option.getOptionGroup()?.getLabel()!);
        for (const subOption of option.getOptionGroup()?.getOptionsList()!) {
          if (subOption?.getLabel()?.toLowerCase().includes(filterValue)) {
            filteredOptionGroup.addOptions(subOption);
          }
        }
        if (filteredOptionGroup.getOptionsList().length > 0) {
          const optionSet = new AutocompleteOptionSet();
          optionSet.setOptionGroup(filteredOptionGroup);
          filteredOptions.push(optionSet);
        }
      } else {
        if (
          option.getOption()?.getLabel()?.toLowerCase().includes(filterValue)
        ) {
          filteredOptions.push(option);
        }
      }
    }
    return filteredOptions;
  }
}
