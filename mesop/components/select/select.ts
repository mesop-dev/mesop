import {MatSelectModule, MatSelectChange} from '@angular/material/select';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  UserEvent,
  Key,
  Type,
  Style,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {
  SelectChangeEvent,
  SelectType,
} from 'mesop/mesop/components/select/select_jspb_proto_pb/mesop/components/select/select_pb';
import {Channel} from '../../web/src/services/channel';
import {formatStyle} from '../../web/src/utils/styles';
import {FormsModule} from '@angular/forms';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  templateUrl: 'select.ng.html',
  standalone: true,
  imports: [MatSelectModule, FormsModule],
})
export class SelectComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: SelectType;
  // In single select mode, the ngModel is a string and not an array.
  selectedOptions: readonly string[] | string = [];
  private initialSelectOptions: readonly string[] = [];

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = SelectType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );

    // In order to preserve backwards compatibility, only update values if the incoming
    // values change.
    //
    // This is to preserve the existing behavior that allows the component to behave
    // reasonably even if the value property is set/updated.
    const values = this._config.getValueList();
    if (this._checkInitialValuesChanged(values)) {
      if (this._config.getMultiple()) {
        this.initialSelectOptions = values;
        this.selectedOptions = values;
      } else {
        this.initialSelectOptions = values;
        this.selectedOptions = values.length > 0 ? values[0] : '';
      }
    }
  }

  config(): SelectType {
    return this._config;
  }

  onSelectOpenedChangeEvent(event: boolean): void {
    const userEvent = new UserEvent();
    userEvent.setBoolValue(event);
    userEvent.setHandlerId(
      this.config().getOnSelectOpenedChangeEventHandlerId()!,
    );
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }

  onSelectSelectionChangeEvent(event: MatSelectChange): void {
    const userEvent = new UserEvent();
    userEvent.setHandlerId(
      this.config().getOnSelectSelectionChangeEventHandlerId()!,
    );
    const changeEvent = new SelectChangeEvent();
    if (typeof event.value === 'string') {
      changeEvent.addValues(event.value);
    } else {
      for (const value of event.value) {
        changeEvent.addValues(value);
      }
    }
    userEvent.setBytesValue(changeEvent.serializeBinary());
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }

  getStyle(): string {
    return formatStyle(this.style);
  }

  getAppearance(): 'fill' | 'outline' {
    return this.config().getAppearance() as 'fill' | 'outline';
  }

  private _checkInitialValuesChanged(
    values: readonly string[] | string,
  ): boolean {
    const valuesOptions = typeof values === 'string' ? [values] : values;
    return (
      JSON.stringify(this.initialSelectOptions.slice().sort()) !==
      JSON.stringify(valuesOptions.slice().sort())
    );
  }
}
