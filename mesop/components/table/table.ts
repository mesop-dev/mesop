import {MatTableModule} from '@angular/material/table';
import {ChangeDetectionStrategy, Component, Input} from '@angular/core';
import {
  TableType,
  TableRow,
  TableClickEvent,
} from 'mesop/mesop/components/table/table_jspb_proto_pb/mesop/components/table/table_pb';
import {Channel} from '../../web/src/services/channel';
import {
  UserEvent,
  Key,
  Type,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';

@Component({
  changeDetection: ChangeDetectionStrategy.Default,
  selector: 'mesop-table',
  templateUrl: 'table.ng.html',
  standalone: true,
  imports: [MatTableModule],
})
export class TableComponent {
  @Input({required: true}) type!: Type;
  @Input() key!: Key;
  private _config!: TableType;
  constructor(private readonly channel: Channel) {}

  ngOnChanges() {
    this._config = TableType.deserializeBinary(
      this.type.getValue() as unknown as Uint8Array,
    );
  }

  config(): TableType {
    return this._config;
  }

  isStickyHeader(): boolean {
    return this._config.getHeader()!.getSticky() || false;
  }

  isStickyColumn(index: number): boolean {
    const columnName = this._config.getDisplayedColumnsList()[index];
    const column = this._config.getColumnsMap().get(columnName);
    return column ? column.getSticky() : false;
  }

  onClickCell(row: TableRow, index: number): void {
    // On cell click events, return the column and row indexes so we can refer back
    // to the same cell on the server.
    const userEvent = new UserEvent();
    userEvent.setHandlerId(this.config().getOnTableClickEventHandlerId()!);
    userEvent.setKey(this.key);
    const clickEvent = new TableClickEvent();
    clickEvent.setColIndex(index);
    // Need to cast to number since the index field is optional, but it should never
    // be null when this event is triggered.
    clickEvent.setRowIndex(row.getIndex() as number);
    userEvent.setBytesValue(clickEvent.serializeBinary());
    this.channel.dispatch(userEvent);
  }
}
