from typing import List

import pytest

from beet import GenericPipeline, PluginError, PluginImportError

TestPipeline = GenericPipeline[List[str]]


def test_empty():
    pipeline = TestPipeline([])
    pipeline.run()
    assert pipeline.ctx == []


def test_basic():
    pipeline = TestPipeline([])

    def p1(ctx: List[str]):
        ctx.append("p1")

    def p2(ctx: List[str]):
        ctx.append("p2")

    pipeline.run([p1, p2])
    assert pipeline.ctx == ["p1", "p2"]


def test_with_yield():
    pipeline = TestPipeline([])

    def p1(ctx: List[str]):
        ctx.append("p1")
        yield
        ctx.append("p1-bis")

    def p2(ctx: List[str]):
        ctx.append("p2")
        yield
        ctx.append("p2-bis")

    pipeline.run([p1, p2])
    assert pipeline.ctx == ["p1", "p2", "p2-bis", "p1-bis"]


def test_with_multiple_yield():
    pipeline = TestPipeline([])

    def p1(ctx: List[str]):
        ctx.append("p1")
        yield
        ctx.append("p1-bis")
        yield
        ctx.append("p1-bis-bis")

    def p2(ctx: List[str]):
        ctx.append("p2")
        yield
        ctx.append("p2-bis")
        yield
        ctx.append("p2-bis-bis")

    pipeline.run([p1, p2])
    assert pipeline.ctx == ["p1", "p2", "p2-bis", "p2-bis-bis", "p1-bis", "p1-bis-bis"]


def test_with_multiple_yield_and_nested_require():
    pipeline = TestPipeline([])

    def p1(ctx: List[str]):
        ctx.append("p1")
        yield
        pipeline.require(p3)
        ctx.append("p1-bis")
        yield
        ctx.append("p1-bis-bis")

    def p2(ctx: List[str]):
        ctx.append("p2")
        yield
        ctx.append("p2-bis")
        yield
        ctx.append("p2-bis-bis")

    def p3(ctx: List[str]):
        ctx.append("p3")
        yield
        ctx.append("p3-bis")

    pipeline.run([p1, p2])
    assert pipeline.ctx == [
        "p1",
        "p2",
        "p2-bis",
        "p2-bis-bis",
        "p3",
        "p1-bis",
        "p1-bis-bis",
        "p3-bis",
    ]


def test_self_require():
    pipeline = TestPipeline([])

    def p1(ctx: List[str]):
        pipeline.require(p1)
        ctx.append("p1")

    pipeline.run([p1])
    assert pipeline.ctx == ["p1"]


def test_error():
    pipeline = TestPipeline([])

    def p1(ctx: List[str]):
        ctx.append("p1")
        yield
        ctx.append("p1-bis")

    def p2(ctx: List[str]):
        raise ValueError("nope")

    with pytest.raises(PluginError):
        pipeline.run([p1, p2])
    assert pipeline.ctx == ["p1"]


def test_error_finally():
    pipeline = TestPipeline([])

    def p1(ctx: List[str]):
        ctx.append("p1")
        try:
            yield
        finally:
            ctx.append("p1-bis")

    def p2(ctx: List[str]):
        ctx.append("p2")
        try:
            yield
        finally:
            ctx.append("p2-bis")

    def p3(ctx: List[str]):
        raise ValueError("nope")

    with pytest.raises(PluginError):
        pipeline.run([p1, p2, p3])
    assert pipeline.ctx == ["p1", "p2", "p2-bis", "p1-bis"]


def test_error_recover():
    pipeline = TestPipeline([])

    def p1(ctx: List[str]):
        ctx.append("p1")
        try:
            yield
        except PluginError as exc:
            ctx.append(str(exc.__cause__))

    def p2(ctx: List[str]):
        raise ValueError("nope")

    pipeline.run([p1, p2])
    assert pipeline.ctx == ["p1", "nope"]


def some_plugin(ctx: List[str]):
    ctx.append("hello")


def test_import_require():
    pipeline = TestPipeline([])
    pipeline.run([f"{__name__}.some_plugin"])
    assert pipeline.ctx == ["hello"]


def test_import_require_not_found():
    pipeline = TestPipeline([])
    dotted_path = f"{__name__}.does_not_exist"

    with pytest.raises(PluginImportError, match=dotted_path):
        pipeline.run([dotted_path])


def test_import_require_whitelist():
    pipeline = TestPipeline([], whitelist=["thing"])
    dotted_path = f"{__name__}.some_plugin"

    with pytest.raises(PluginImportError, match=dotted_path):
        pipeline.run([dotted_path])


def test_import_require_whitelist_match():
    dotted_path = f"{__name__}.some_plugin"
    pipeline = TestPipeline([], whitelist=[dotted_path])

    pipeline.run([dotted_path])
    assert pipeline.ctx == ["hello"]
