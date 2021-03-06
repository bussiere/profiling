# -*- coding: utf-8 -*-
import pickle

import pytest

from profiling.profiler import make_code
from profiling.sortkeys import by_calls, by_name, by_total_time_per_call
from profiling.stats import (
    FrozenStat, RecordingStat, RecordingStatistics, Stat, VoidRecordingStat)


def test_stat():
    stat = Stat(name='foo', filename='bar', lineno=42)
    assert stat.regular_name == 'foo'
    stat.module = 'baz'
    assert stat.regular_name == 'baz:foo'
    assert stat.total_time_per_call == 0
    stat.total_time = 128
    stat.calls = 4
    assert stat.total_time_per_call == 32
    assert len(stat) == 0
    assert not list(stat)


def test_recording():
    stats = RecordingStatistics()
    with pytest.raises(TypeError):
        stats.record_entering()
    with pytest.raises(TypeError):
        stats.record_leaving()
    stats.wall = lambda: 10
    stats.record_starting(0)
    code = make_code('foo')
    stat = RecordingStat(code)
    assert stat.name == 'foo'
    assert stat.calls == 0
    assert stat.total_time == 0
    stat.record_entering(100)
    stat.record_leaving(200)
    assert stat.calls == 1
    assert stat.total_time == 100
    stat.record_entering(200)
    stat.record_leaving(400)
    assert stat.calls == 2
    assert stat.total_time == 300
    code2 = make_code('bar')
    stat2 = RecordingStat(code2)
    assert code2 not in stat
    stat.add_child(code2, stat2)
    assert code2 in stat
    assert stat.get_child(code2) is stat2
    assert len(stat) == 1
    assert list(stat) == [stat2]
    assert stat.total_time == 300
    assert stat.own_time == 300
    stat2.record_entering(1000)
    stat2.record_leaving(1004)
    assert stat2.total_time == 4
    assert stat2.own_time == 4
    assert stat.total_time == 300
    assert stat.own_time == 296
    stat.clear()
    assert len(stat) == 0
    with pytest.raises(TypeError):
        pickle.dumps(stat)
    stat3 = stat.ensure_child(make_code('baz'))
    assert isinstance(stat3, VoidRecordingStat)
    stats.wall = lambda: 2000
    stats.record_stopping(400)
    assert stats.cpu_time == 400
    assert stats.wall_time == 1990
    assert stats.cpu_usage == 400 / 1990.


def test_frozen():
    code = make_code('foo')
    stat = RecordingStat(code)
    stat.record_entering(0)
    stat.record_leaving(10)
    assert stat.name == 'foo'
    assert stat.total_time == 10
    frozen_stat = FrozenStat(stat)
    with pytest.raises(AttributeError):
        frozen_stat.record_entering(0)
    assert frozen_stat.name == 'foo'
    assert frozen_stat.total_time == 10
    restored_frozen_stat = pickle.loads(pickle.dumps(frozen_stat))
    assert restored_frozen_stat.name == 'foo'
    assert restored_frozen_stat.total_time == 10


def test_sorting():
    stat = RecordingStat(make_code('foo'))
    stat1 = RecordingStat(make_code('bar'))
    stat2 = RecordingStat(make_code('baz'))
    stat3 = RecordingStat(make_code('qux'))
    stat.add_child(stat1.code, stat1)
    stat.add_child(stat2.code, stat2)
    stat.add_child(stat3.code, stat3)
    stat.total_time = 100
    stat1.total_time = 20
    stat1.calls = 3
    stat2.total_time = 30
    stat2.calls = 2
    stat3.total_time = 40
    stat3.calls = 4
    assert stat.sorted() == [stat3, stat2, stat1]
    assert stat.sorted(by_calls) == [stat3, stat1, stat2]
    assert stat.sorted(by_total_time_per_call) == [stat2, stat3, stat1]
    assert stat.sorted(by_name) == [stat1, stat2, stat3]
