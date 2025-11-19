import {
  Component,
  ComponentDiff,
} from 'mesop/mesop/protos/ui_jspb_proto_pb/mesop/protos/ui_pb';

/** Updates the given component in place with the provided diffs. */
export function applyComponentDiff(component: Component, diff: ComponentDiff) {
  if (
    diff.getUpdateStrategyKey() ===
    ComponentDiff.UpdateStrategy.UPDATE_STRATEGY_REPLACE
  ) {
    component.setKey(diff.getKey());
  }
  if (
    diff.getUpdateStrategySourceCodeLocation() ===
    ComponentDiff.UpdateStrategy.UPDATE_STRATEGY_REPLACE
  ) {
    component.setSourceCodeLocation(diff.getSourceCodeLocation());
  }
  if (
    diff.getUpdateStrategyStyle() ===
    ComponentDiff.UpdateStrategy.UPDATE_STRATEGY_REPLACE
  ) {
    component.setStyle(diff.getStyle());
  }
  if (
    diff.getUpdateStrategyStyleDebugJson() ===
    ComponentDiff.UpdateStrategy.UPDATE_STRATEGY_REPLACE
  ) {
    component.setStyleDebugJson(diff.getStyleDebugJson() as string);
  }
  if (
    diff.getUpdateStrategyType() ===
    ComponentDiff.UpdateStrategy.UPDATE_STRATEGY_REPLACE
  ) {
    component.setType(diff.getType());
  }

  let deleteIndex = -1;
  for (const childDiff of diff.getChildrenList()) {
    if (childDiff.getDiffType() === ComponentDiff.DiffType.DIFF_TYPE_UPDATE) {
      applyComponentDiff(
        component.getChildrenList()[childDiff.getIndex() as number],
        childDiff,
      );
    } else if (
      // We do not care about adding the node to a specific index since we expect
      // additions to be added in order after all updates.
      //
      // Once deletions are applied, the additions should be at the expected location
      // in the component tree.
      childDiff.getDiffType() === ComponentDiff.DiffType.DIFF_TYPE_ADD
    ) {
      component.addChildren(childDiff.getComponent());
    } else if (
      childDiff.getDiffType() === ComponentDiff.DiffType.DIFF_TYPE_DELETE &&
      (deleteIndex === -1 || (childDiff.getIndex() as number) < deleteIndex)
    ) {
      // Only track the smallest `deleteIndex` if there are deletions. See comment
      // below.
      deleteIndex = childDiff.getIndex() as number;
    }
  }

  // If deleteIndex is set to a non-negative number, this means that we have child nodes
  // to delete.
  //
  // Due to the way deletes are determined, we know that deletes will always occur
  // sequentially to the end of the list. This allows us to delete all nodes after the
  // lowest `deleteIndex` found.
  if (deleteIndex !== -1) {
    component.setChildrenList(
      component.getChildrenList().slice(0, deleteIndex),
    );
  }
}

const STATE_DIFF_VALUES_CHANGED = 'values_changed';
const STATE_DIFF_TYPE_CHANGES = 'type_changes';
const STATE_DIFF_DATA_FRAME_CHANGED = 'data_frame_changed';
const STATE_DIFF_EQUALITY_CHANGED = 'mesop_equality_changed';
const STATE_DIFF_ITERABLE_ITEM_REMOVED = 'iterable_item_removed';
const STATE_DIFF_ITERABLE_ITEM_ADDED = 'iterable_item_added';
const STATE_DIFF_SET_ITEM_REMOVED = 'set_item_removed';
const STATE_DIFF_SET_ITEM_ADDED = 'set_item_added';
const STATE_DIFF_DICT_ITEM_REMOVED = 'dictionary_item_removed';
const STATE_DIFF_DICT_ITEM_ADDED = 'dictionary_item_added';
const STATE_DIFF_ITERABLE_ITEMS_INSERTED = 'iterable_items_inserted';
const STATE_DIFF_ITERABLE_ITEMS_REMOVED = 'iterable_items_deleted';

// Interface for state diff objects.
interface StateDiff {
  path: (string | number)[];
  action: string;
  value: any;
  t2_from_index?: number;
  t2_to_index?: number;
}

// Applies state diffs to the state object.
export function applyStateDiff(stateJson: string, diffJson: string): string {
  // An empty array indicates no changes, so no need to apply diffs.
  if (diffJson === '[]') {
    return stateJson;
  }

  const root = JSON.parse(stateJson) as object;
  const diff = JSON.parse(diffJson) as StateDiff[];

  // Handle array deletions first. Deletions will appear in the diffs from lowest index
  // to highest index. To ensure indexes do not get moved, we perform deletions in
  // reverse.
  for (let i = diff.length - 1; i >= 0; i--) {
    if (diff[i].action === STATE_DIFF_ITERABLE_ITEM_REMOVED) {
      removeArrayValue(root, diff[i].path);
    }
  }

  // Apply the rest of the diffs.
  for (const row of diff) {
    if (
      row.action === STATE_DIFF_VALUES_CHANGED ||
      row.action === STATE_DIFF_TYPE_CHANGES ||
      row.action === STATE_DIFF_DATA_FRAME_CHANGED ||
      row.action === STATE_DIFF_EQUALITY_CHANGED
    ) {
      updateValue(root, row.path, row.value);
    } else if (row.action === STATE_DIFF_DICT_ITEM_ADDED) {
      updateObjectValue(root, row.path, row.value);
    } else if (row.action === STATE_DIFF_DICT_ITEM_REMOVED) {
      removeObjectValue(root, row.path);
    } else if (row.action === STATE_DIFF_ITERABLE_ITEM_ADDED) {
      addArrayValue(root, row.path, row.value);
    } else if (row.action === STATE_DIFF_SET_ITEM_ADDED) {
      addSetValue(root, row.path, row.value);
    } else if (row.action === STATE_DIFF_SET_ITEM_REMOVED) {
      removeSetValue(root, row.path, row.value);
    } else if (
      row.action === STATE_DIFF_ITERABLE_ITEMS_INSERTED &&
      row.t2_from_index !== undefined &&
      row.t2_to_index !== undefined
    ) {
      insertIterableItems(
        root,
        row.path,
        row.value,
        row.t2_from_index,
        row.t2_to_index,
      );
    } else if (
      row.action === STATE_DIFF_ITERABLE_ITEMS_REMOVED &&
      row.t2_from_index !== undefined &&
      row.t2_to_index !== undefined
    ) {
      deleteIterableItems(root, row.path, row.t2_from_index, row.t2_to_index);
    }
  }

  return JSON.stringify(root);
}

// Updates value at path.
function updateValue(root: object, path: (string | number)[], value: any) {
  let objectSegment = root;
  for (let i = 0; i < path.length; ++i) {
    if (i + 1 === path.length) {
      // @ts-ignore: Ignore type
      objectSegment[path[i]] = value;
    } else {
      // @ts-ignore: Ignore type
      objectSegment = objectSegment[path[i]];
    }
  }
}

// Adds item to the array at path.
function addArrayValue(root: object, path: (string | number)[], value: any) {
  const objectSegment = getLastObjectSegment(root, path);
  if (objectSegment) {
    // @ts-ignore: Ignore type
    objectSegment.splice(path[path.length - 1], 0, value);
  }
}

// Removes item from array at path.
function removeArrayValue(root: object, path: (string | number)[]) {
  let objectSegment = root;
  for (let i = 0; i < path.length; ++i) {
    if (i + 1 === path.length) {
      // @ts-ignore: Ignore type
      objectSegment.splice(path[i], 1);
    } else {
      // @ts-ignore: Ignore type
      objectSegment = objectSegment[path[i]];
    }
  }
}

// Adds item from the set at path.
function addSetValue(root: object, path: (string | number)[], value: any) {
  const objectSegment = getLastObjectSegment(root, path);
  if (objectSegment) {
    // @ts-ignore: Ignore type
    objectSegment[path[path.length - 1]].push(value);
  }
}

// Removes item from the set at path.
function removeSetValue(root: object, path: (string | number)[], value: any) {
  const objectSegment = getLastObjectSegment(root, path);
  if (objectSegment) {
    // @ts-ignore: Ignore type
    const set = new Set(objectSegment[path[path.length - 1]]);
    set.delete(value);
    // @ts-ignore: Ignore type
    objectSegment[path[path.length - 1]] = [...set];
  }
}

// Adds/Updates value to object at path.
function updateObjectValue(
  root: object,
  path: (string | number)[],
  value: any,
) {
  let objectSegment = root;
  for (let i = 0; i < path.length; ++i) {
    if (i + 1 === path.length) {
      // @ts-ignore: Ignore type
      objectSegment[path[i]] = value;
    } else {
      // @ts-ignore: Ignore type
      objectSegment = objectSegment[path[i]];
    }
  }
}

// Removes value from object at path.
function removeObjectValue(root: object, path: (string | number)[]) {
  let objectSegment = root;
  for (let i = 0; i < path.length; ++i) {
    if (i + 1 === path.length) {
      // @ts-ignore: Ignore type
      delete objectSegment[path[i]];
    } else {
      // @ts-ignore: Ignore type
      objectSegment = objectSegment[path[i]];
    }
  }
}

// Inserts iterable items
function insertIterableItems(
  root: object,
  path: (string | number)[],
  value: any,
  from_index: number,
  to_index: number,
) {
  let objectSegment = root;
  for (let i = 0; i < path.length; ++i) {
    if (i + 1 === path.length) {
      // @ts-ignore: Ignore type
      objectSegment[path[i]].splice(from_index, 0, ...value);
    } else {
      // @ts-ignore: Ignore type
      objectSegment = objectSegment[path[i]];
    }
  }
}

// Delete iterable items
function deleteIterableItems(
  root: object,
  path: (string | number)[],
  from_index: number,
  to_index: number,
) {
  let objectSegment = root;
  for (let i = 0; i < path.length; ++i) {
    if (i + 1 === path.length) {
      // @ts-ignore: Ignore type
      // @ts-ignore: Ignore type
      objectSegment[path[i]].splice(from_index, to_index - from_index + 1);
    } else {
      // @ts-ignore: Ignore type
      objectSegment = objectSegment[path[i]];
    }
  }
}

// Helper function for retrieving the last segment from a given path.
function getLastObjectSegment(
  root: object,
  path: (string | number)[],
): object | null {
  let objectSegment = root;
  for (let i = 0; i < path.length; ++i) {
    if (i + 1 === path.length) {
      return objectSegment;
    }
    // Edge case where the array does not exist yet, so we need to create an array
    // before we can append.
    //
    // @ts-ignore: Ignore type
    if (objectSegment[path[i]] === undefined && i + 2 === path.length) {
      // @ts-ignore: Ignore type
      objectSegment[path[i]] = [];
    }
    // @ts-ignore: Ignore type
    objectSegment = objectSegment[path[i]];
  }
  return null;
}
