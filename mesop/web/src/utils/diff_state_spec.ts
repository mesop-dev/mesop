import {applyStateDiff} from 'mesop/mesop/web/src/utils/diff';

describe('applyStateDiff functionality', () => {
  it('applies no diffs when there are no diffs', () => {
    const state = JSON.stringify({
      val1: 1,
    });
    expect(applyStateDiff(state, '[]')).toBe(state);
  });

  it('applies updates to primitives', () => {
    const state1 = JSON.stringify({
      val1: 'val1',
      val2: 1,
      val3: 1.1,
      val4: true,
      val5: true,
    });
    const diff = JSON.stringify([
      {
        path: ['val5'],
        action: 'type_changes',
        value: null,
        type: "<class 'NoneType'>",
        old_type: "<class 'bool'>",
      },
      {path: ['val1'], action: 'values_changed', value: 'VAL1'},
      {path: ['val2'], action: 'values_changed', value: 2},
      {path: ['val3'], action: 'values_changed', value: 1.2},
      {path: ['val4'], action: 'values_changed', value: false},
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        val1: 'VAL1',
        val2: 2,
        val3: 1.2,
        val4: false,
        val5: null,
      }),
    );
  });

  it('applies updates to core data structures', () => {
    const state1 = JSON.stringify({
      val1: [1, 2, 3],
      val2: {k1: 'v1'},
      val3: ['t1', 't2'],
    });
    const diff = JSON.stringify([
      {
        path: ['val2', 'k2'],
        value: 'v2',
        action: 'dictionary_item_added',
      },
      {
        path: ['val2', 'k1'],
        value: 'v1',
        action: 'dictionary_item_removed',
      },
      {path: ['val3', 0], action: 'values_changed', value: 't2'},
      {path: ['val3', 1], action: 'values_changed', value: 't1'},
      {path: ['val1', 2], value: 4, action: 'iterable_item_added'},
      {path: ['val1', 0], value: 1, action: 'iterable_item_removed'},
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        val1: [2, 3, 4],
        val2: {k2: 'v2'},
        val3: ['t2', 't1'],
      }),
    );
  });

  it('applies type change updates', () => {
    const state1 = JSON.stringify({
      val1: 'String',
    });
    const diff = JSON.stringify([
      {
        path: ['val1'],
        action: 'type_changes',
        value: true,
        type: "<class 'bool'>",
        old_type: "<class 'str'>",
      },
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        val1: true,
      }),
    );
  });

  it('applies multiple dict changes', () => {
    const state1 = JSON.stringify({
      val1: {
        k1: 'v1',
        k2: 'v2',
        k3: 'v3',
      },
    });
    const diff = JSON.stringify([
      {
        path: ['val1', 'k4'],
        value: 'v4',
        action: 'dictionary_item_added',
      },
      {
        path: ['val1', 'k5'],
        value: 'v5',
        action: 'dictionary_item_added',
      },
      {
        path: ['val1', 'k3'],
        value: 'v3',
        action: 'dictionary_item_removed',
      },
      {path: ['val1', 'k1'], action: 'values_changed', value: 'V1'},
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        val1: {
          k1: 'V1',
          k2: 'v2',
          k4: 'v4',
          k5: 'v5',
        },
      }),
    );
  });

  it('applies updates to nested changes', () => {
    const state1 = JSON.stringify({
      val1: {
        k1: [{val1: [1, 2, 3]}, {val1: [1]}],
        k2: [],
        k3: [{val1: []}],
      },
    });

    const diff = JSON.stringify([
      {
        path: ['val1', 'k4', 0],
        value: {val1: []},
        action: 'iterable_item_added',
      },
      {
        path: ['val1', 'k3'],
        value: [{val1: []}],
        action: 'dictionary_item_removed',
      },
      {
        path: ['val1', 'k1', 1, 'val1', 0],
        action: 'values_changed',
        value: 3,
      },
      {
        path: ['val1', 'k1', 1, 'val1', 1],
        value: 4,
        action: 'iterable_item_added',
      },
      {
        path: ['val1', 'k1', 1, 'val1', 2],
        value: 6,
        action: 'iterable_item_added',
      },
      {
        path: ['val1', 'k1', 1, 'val1', 3],
        value: '2',
        action: 'iterable_item_added',
      },
      {
        path: ['val1', 'k2', 0],
        value: {val1: [2, 2]},
        action: 'iterable_item_added',
      },
      {
        path: ['val1', 'k1', 0, 'val1', 2],
        value: 3,
        action: 'iterable_item_removed',
      },
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        val1: {
          k1: [{val1: [1, 2]}, {val1: [3, 4, 6, '2']}],
          k2: [{val1: [2, 2]}],
          k4: [{val1: []}],
        },
      }),
    );
  });

  it('applies updates for weird str dict keys', () => {
    const state1 = JSON.stringify({
      val1: {'k-1': 'v1', 'k.2': 'v2', 'k 3': 'v3'},
    });

    const diff = JSON.stringify([
      {path: ['val1', 'k-1'], action: 'values_changed', value: 'V1'},
      {path: ['val1', 'k 3'], action: 'values_changed', value: 'v4'},
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        val1: {'k-1': 'V1', 'k.2': 'v2', 'k 3': 'v4'},
      }),
    );
  });

  it('applies updates to int dict keys', () => {
    const state1 = JSON.stringify({
      val1: {
        '1': 'v1',
        '2': 'v2',
        '3': 'v3',
      },
    });
    const diff = JSON.stringify([
      {path: ['val1', 1], action: 'values_changed', value: 'V1'},
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        val1: {
          '1': 'V1',
          '2': 'v2',
          '3': 'v3',
        },
      }),
    );
  });

  it('applies multiple array changes', () => {
    const state1 = JSON.stringify({
      val1: [1, 2, 3, 4, 5, 6, 7],
    });
    const diff = JSON.stringify([
      {path: ['val1', 2], value: 3, action: 'iterable_item_added'},
      {path: ['val1', 0], value: 1, action: 'iterable_item_removed'},
      {path: ['val1', 4], value: 5, action: 'iterable_item_removed'},
      {path: ['val1', 6], value: 7, action: 'iterable_item_removed'},
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        val1: [2, 3, 3, 4, 6],
      }),
    );
  });

  it('applies multiple array deletions', () => {
    const state1 = JSON.stringify({
      val1: [1, 2, 3, 4, 5, 6, 7],
      val2: {
        val2A: [10, 20, 30, 40, 50, 60, 70],
      },
    });
    const diff = JSON.stringify([
      {path: ['val1', 0], value: 1, action: 'iterable_item_removed'},
      {path: ['val1', 2], value: 3, action: 'iterable_item_removed'},
      {path: ['val1', 4], value: 5, action: 'iterable_item_removed'},
      {
        path: ['val2', 'val2A', 2],
        value: 30,
        action: 'iterable_item_removed',
      },
      {
        path: ['val2', 'val2A', 4],
        value: 50,
        action: 'iterable_item_removed',
      },
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        val1: [2, 4, 6, 7],
        val2: {
          val2A: [10, 20, 40, 60, 70],
        },
      }),
    );
  });

  it('applies data frame updates', () => {
    const state1 = JSON.stringify({
      data: {
        '__pandas.DataFrame__':
          '{"schema":{"fields":[{"name":"index","type":"integer"},{"name":"Strings","type":"string"}],"primaryKey":["index"],"pandas_version":"1.4.0"},"data":[{"index":0,"Strings":"Hello"},{"index":1,"Strings":"World"}]}',
      },
    });
    const diff = JSON.stringify([
      {
        path: ['data'],
        action: 'data_frame_changed',
        value: {
          '__pandas.DataFrame__':
            '{"schema":{"fields":[{"name":"index","type":"integer"},{"name":"Strings","type":"string"}],"primaryKey":["index"],"pandas_version":"1.4.0"},"data":[{"index":0,"Strings":"Hello"},{"index":1,"Strings":"Universe"}]}',
        },
      },
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        data: {
          '__pandas.DataFrame__':
            '{"schema":{"fields":[{"name":"index","type":"integer"},{"name":"Strings","type":"string"}],"primaryKey":["index"],"pandas_version":"1.4.0"},"data":[{"index":0,"Strings":"Hello"},{"index":1,"Strings":"Universe"}]}',
        },
      }),
    );
  });

  it('applies updates to bytes', () => {
    const state1 = JSON.stringify({
      data: {
        '__python.bytes__': 'aGVsbG8gd29ybGQ=',
      },
    });
    const diff = JSON.stringify([
      {
        path: ['data'],
        action: 'values_changed',
        value: {
          '__python.bytes__': 'VGhpcyBpcyBhIHRlc3Q=',
        },
      },
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        data: {
          '__python.bytes__': 'VGhpcyBpcyBhIHRlc3Q=',
        },
      }),
    );
  });

  it('applies updates to list of datetime objects', () => {
    const state1 = JSON.stringify({
      dates: [],
    });

    const diff = JSON.stringify([
      {
        'path': ['dates', 0],
        'value': {'__datetime.datetime__': '2024-12-05T00:00:00+05:30'},
        'action': 'iterable_item_added',
      },
      {
        'path': ['dates', 1],
        'value': {'__datetime.datetime__': '1972-02-02T00:00:00+00:00'},
        'action': 'iterable_item_added',
      },
      {
        'path': ['dates', 2],
        'value': {'__datetime.datetime__': '2005-10-12T00:00:00-05:00'},
        'action': 'iterable_item_added',
      },
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        dates: [
          {'__datetime.datetime__': '2024-12-05T00:00:00+05:30'},
          {'__datetime.datetime__': '1972-02-02T00:00:00+00:00'},
          {'__datetime.datetime__': '2005-10-12T00:00:00-05:00'},
        ],
      }),
    );
  });

  it('applies UploadedFile updates', () => {
    const state1 = JSON.stringify({
      data: {
        '__mesop.UploadedFile__': {
          'contents': '',
          'name': '',
          'size': 0,
          'mime_type': '',
        },
      },
    });
    const diff = JSON.stringify([
      {
        path: ['data'],
        action: 'mesop_equality_changed',
        value: {
          '__mesop.UploadedFile__': {
            'contents': 'data',
            'name': 'file.png',
            'size': 10,
            'mime_type': 'image/png',
          },
        },
      },
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        data: {
          '__mesop.UploadedFile__': {
            'contents': 'data',
            'name': 'file.png',
            'size': 10,
            'mime_type': 'image/png',
          },
        },
      }),
    );
  });

  it('applies updates to sets', () => {
    const state1 = JSON.stringify({
      data: {
        '__python.set__': [1, 3, 5],
      },
    });
    const diff = JSON.stringify([
      {
        path: ['data', '__python.set__'],
        action: 'set_item_added',
        value: 4,
      },
      {
        path: ['data', '__python.set__'],
        action: 'set_item_removed',
        value: 1,
      },
      {
        path: ['data', '__python.set__'],
        action: 'set_item_added',
        value: 7,
      },
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        data: {
          '__python.set__': [3, 5, 4, 7],
        },
      }),
    );
  });

  it('applies multiple iterable changes', () => {
    const state1 = JSON.stringify({
      val1: [1, 2, 3, 4, 5, 6, 7],
    });
    const diff = JSON.stringify([
      {
        'path': ['val1'],
        'action': 'iterable_items_deleted',
        'value': [],
        'old_value': [1],
        'type': "<class 'list'>",
        'old_type': "<class 'list'>",
        'new_path': null,
        't1_from_index': 0,
        't1_to_index': 1,
        't2_from_index': 0,
        't2_to_index': 0,
      },
      {
        'path': ['val1'],
        'action': 'iterable_items_equal',
        'value': null,
        'old_value': null,
        'type': "<class 'NoneType'>",
        'old_type': "<class 'NoneType'>",
        'new_path': null,
        't1_from_index': 1,
        't1_to_index': 3,
        't2_from_index': 0,
        't2_to_index': 2,
      },
      {
        'path': ['val1'],
        'action': 'iterable_items_inserted',
        'value': [3],
        'old_value': [],
        'type': "<class 'list'>",
        'old_type': "<class 'list'>",
        'new_path': null,
        't1_from_index': 3,
        't1_to_index': 3,
        't2_from_index': 2,
        't2_to_index': 3,
      },
      {
        'path': ['val1'],
        'action': 'iterable_items_equal',
        'value': null,
        'old_value': null,
        'type': "<class 'NoneType'>",
        'old_type': "<class 'NoneType'>",
        'new_path': null,
        't1_from_index': 3,
        't1_to_index': 4,
        't2_from_index': 3,
        't2_to_index': 4,
      },
      {
        'path': ['val1'],
        'action': 'iterable_items_deleted',
        'value': [],
        'old_value': [5],
        'type': "<class 'list'>",
        'old_type': "<class 'list'>",
        'new_path': null,
        't1_from_index': 4,
        't1_to_index': 5,
        't2_from_index': 4,
        't2_to_index': 4,
      },
      {
        'path': ['val1'],
        'action': 'iterable_items_equal',
        'value': null,
        'old_value': null,
        'type': "<class 'NoneType'>",
        'old_type': "<class 'NoneType'>",
        'new_path': null,
        't1_from_index': 5,
        't1_to_index': 6,
        't2_from_index': 4,
        't2_to_index': 5,
      },
      {
        'path': ['val1'],
        'action': 'iterable_items_deleted',
        'value': [],
        'old_value': [7],
        'type': "<class 'list'>",
        'old_type': "<class 'list'>",
        'new_path': null,
        't1_from_index': 6,
        't1_to_index': 7,
        't2_from_index': 5,
        't2_to_index': 5,
      },
    ]);

    expect(applyStateDiff(state1, diff)).toBe(
      JSON.stringify({
        val1: [2, 3, 3, 4, 6],
      }),
    );
  });
});
