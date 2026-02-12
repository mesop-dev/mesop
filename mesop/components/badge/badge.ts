import {MatBadgeModule} from '@angular/material/badge';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Key,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {BadgeType} from 'mesop/mesop/components/badge/badge_jspb_proto_pb/mesop/components/badge/badge_pb';
import {Channel} from '../../web/src/services/channel';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  templateUrl: 'badge.ng.html',
  standalone: true,
  imports: [MatBadgeModule],
})
export class BadgeComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  private _config!: BadgeType;

  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = BadgeType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): BadgeType {
    return this._config;
  }

  getColor(): 'primary' | 'accent' | 'warn' {
    return this.config().getColor() as 'primary' | 'accent' | 'warn';
  }

  getPosition():
    | 'above after'
    | 'above before'
    | 'below before'
    | 'below after'
    | 'before'
    | 'after'
    | 'above'
    | 'below' {
    return this.config().getPosition() as
      | 'above after'
      | 'above before'
      | 'below before'
      | 'below after'
      | 'before'
      | 'after'
      | 'above'
      | 'below';
  }

  getSize(): 'small' | 'medium' | 'large' {
    return this.config().getSize() as 'small' | 'medium' | 'large';
  }
}
