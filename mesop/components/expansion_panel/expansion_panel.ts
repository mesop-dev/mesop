import {MatIconModule} from '@angular/material/icon';
import {MatExpansionModule} from '@angular/material/expansion';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  Style,
  Key,
  Type,
  UserEvent,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';
import {ExpansionPanelType} from 'mesop/mesop/components/expansion_panel/expansion_panel_jspb_proto_pb/mesop/components/expansion_panel/expansion_panel_pb';
import {Channel} from '../../web/src/services/channel';
import {formatStyle} from '../../web/src/utils/styles';

type ExpansionPanelEnabledState = 'None' | 'True' | 'False';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-expansion-panel',
  templateUrl: 'expansion_panel.ng.html',
  standalone: true,
  styleUrl: 'expansion_panel.css',
  imports: [MatExpansionModule, MatIconModule],
})
export class ExpansionPanelComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  @Input() style!: Style;
  private _config!: ExpansionPanelType;
  private initialPanelState: ExpansionPanelEnabledState = 'False';
  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = ExpansionPanelType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );

    if (
      this.initialPanelState !==
      (this._config.getExpanded()! as ExpansionPanelEnabledState)
    ) {
      this.initialPanelState =
        this._config.getExpanded()! as ExpansionPanelEnabledState;
    }
  }

  config(): ExpansionPanelType {
    return this._config;
  }

  expanded(): boolean | undefined {
    if (this._config.getExpanded() === 'True') {
      return true;
    }
    if (this._config.getExpanded() === 'False') {
      return false;
    }
    return undefined;
  }

  onPanelOpened(): void {
    if (this.initialPanelState === 'True') {
      return;
    }
    const userEvent = new UserEvent();
    userEvent.setHandlerId(this.config().getOnToggleHandlerId()!);
    userEvent.setKey(this.key);
    userEvent.setBoolValue(true);
    this.channel.dispatch(userEvent);
  }

  onPanelClosed(): void {
    if (this.initialPanelState === 'False') {
      return;
    }
    const userEvent = new UserEvent();
    userEvent.setHandlerId(this.config().getOnToggleHandlerId()!);
    userEvent.setKey(this.key);
    userEvent.setBoolValue(false);
    this.channel.dispatch(userEvent);
  }

  getStyle(): string {
    return formatStyle(this.style);
  }
}
