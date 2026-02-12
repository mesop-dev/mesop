import {MatAccordion} from '@angular/material/expansion';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {AccordionType} from 'mesop/mesop/components/accordion/accordion_jspb_proto_pb/mesop/components/accordion/accordion_pb';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-accordion',
  templateUrl: 'accordion.ng.html',
  standalone: true,
  imports: [MatAccordion],
})
export class AccordionComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  private _config!: AccordionType;

  ngOnChanges() {
    this._config = AccordionType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): AccordionType {
    return this._config;
  }
}
