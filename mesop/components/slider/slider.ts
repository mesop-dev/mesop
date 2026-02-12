import {MatSliderModule} from '@angular/material/slider';
import {FormsModule} from '@angular/forms';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  UserEvent,
  Key,
  Type,
  Style,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {SliderType} from 'mesop/mesop/components/slider/slider_jspb_proto_pb/mesop/components/slider/slider_pb';
import {Channel} from '../../web/src/services/channel';
import {debounceTime} from 'rxjs/operators';
import {Subject} from 'rxjs';
import {formatStyle} from '../../web/src/utils/styles';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  templateUrl: 'slider.ng.html',
  standalone: true,
  imports: [MatSliderModule, FormsModule],
})
export class SliderComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;

  // Need to make this value accessible by ngModel.
  value = 0;

  private _config!: SliderType;
  private changeSubject = new Subject<number>();
  private cachedSliderInitialValue?: number = 0;

  constructor(private readonly channel: Channel) {
    this.changeSubject
      .pipe(debounceTime(300))
      .subscribe((number) => this.onValueChangeDebounced(number));
  }

  ngOnChanges() {
    this._config = SliderType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
    this.updateValue();
  }

  config(): SliderType {
    return this._config;
  }

  updateValue(): void {
    // Cache initial slider value since we only want to update the slider position
    // if the value has changed on the server side. This allows the user to change
    // the slider position, but still allows the server to set a default value or update
    // the value programmatically.
    //
    // This emulates behavior similar to the value attribute on the input and
    // textarea components.
    if (this.cachedSliderInitialValue !== this._config.getValue()) {
      this.cachedSliderInitialValue = this._config.getValue();
      this.value = this._config.getValue() as number;
    }
  }

  getColor(): 'primary' | 'accent' | 'warn' {
    return this.config().getColor() as 'primary' | 'accent' | 'warn';
  }

  onValueChange(value: number): void {
    this.changeSubject.next(value);
    this.value = value;
  }

  onValueChangeDebounced(value: number) {
    const userEvent = new UserEvent();
    this.value = value;
    userEvent.setHandlerId(this.config().getOnValueChangeHandlerId()!);
    userEvent.setDoubleValue(value);
    userEvent.setKey(this.key);
    this.channel.dispatch(userEvent);
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
