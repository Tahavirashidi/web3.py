import itertools
import pytest
import sys

from web3.manager import (
    RequestManager,
)
from web3.providers import (
    BaseProvider,
)


def test_provider_property_setter_and_getter(middleware_factory):
    provider = BaseProvider()

    middleware_a = middleware_factory()
    middleware_b = middleware_factory()
    middleware_c = middleware_factory()
    assert middleware_a is not middleware_b
    assert middleware_a is not middleware_c

    manager = RequestManager(None, provider, middlewares=[])

    assert manager.middlewares == tuple()

    manager.middleware_stack.add(middleware_a)
    manager.middleware_stack.add(middleware_b)

    manager.middleware_stack.clear()

    assert manager.middlewares == tuple()

    manager.middleware_stack.add(middleware_c)
    manager.middleware_stack.add(middleware_b)
    manager.middleware_stack.add(middleware_a)

    with pytest.raises(ValueError):
        manager.middleware_stack.add(middleware_b)

    assert manager.middlewares == (
        middleware_a,
        middleware_b,
        middleware_c,
    )


@pytest.mark.skipif(sys.version_info.major < 3, reason="Mock requires Py 3")
def test_modifying_middleware_regenerates_request_functions(middleware_factory):
    from unittest.mock import Mock

    # setup
    provider = BaseProvider()
    manager = RequestManager(None, provider)
    manager._generate_request_functions = Mock(wraps=manager._generate_request_functions)

    # count number of middleware rebuilds
    counter = itertools.count()

    def assert_one_more_rebuild():
        assert manager._generate_request_functions.call_count == next(counter)
    assert_one_more_rebuild()  # assert zero rebuilds, to start

    # manual call
    manager._generate_request_functions()

    assert_one_more_rebuild()

    # reset
    manager.middlewares = []

    assert_one_more_rebuild()

    # add
    manager.middleware_stack.add(middleware_factory(), 'a')

    assert_one_more_rebuild()

    # replace
    manager.middleware_stack.replace('a', middleware_factory())

    assert_one_more_rebuild()

    # remove
    manager.middleware_stack.remove('a')

    assert_one_more_rebuild()

    # clear
    manager.middleware_stack.clear()

    assert_one_more_rebuild()


def test_add_named_middleware(middleware_factory):
    mw = middleware_factory()
    manager = RequestManager(None, BaseProvider(), middlewares=[(mw, 'the-name')])
    assert len(manager.middlewares) == 1

    assert manager.middlewares == (mw, )


def test_add_named_duplicate_middleware(middleware_factory):
    mw = middleware_factory()
    manager = RequestManager(None, BaseProvider(), middlewares=[(mw, 'the-name'), (mw, 'name2')])
    assert manager.middlewares == (mw, mw)

    manager.middleware_stack.clear()
    assert len(manager.middlewares) == 0

    manager.middleware_stack.add(mw, 'name1')
    manager.middleware_stack.add(mw, 'name2')
    assert manager.middlewares == (mw, mw)


def test_add_duplicate_middleware(middleware_factory):
    mw = middleware_factory()
    with pytest.raises(ValueError):
        manager = RequestManager(None, BaseProvider(), middlewares=[mw, mw])

    manager = RequestManager(None, BaseProvider(), middlewares=[])
    manager.middleware_stack.add(mw)

    with pytest.raises(ValueError):
        manager.middleware_stack.add(mw)
    assert manager.middlewares == (mw, )


def test_replace_middleware(middleware_factory):
    mw1 = middleware_factory()
    mw2 = middleware_factory()
    mw3 = middleware_factory()

    manager = RequestManager(None, BaseProvider(), middlewares=[mw1, (mw2, '2nd'), mw3])

    assert manager.middlewares == (mw1, mw2, mw3)

    mw_replacement = middleware_factory()
    manager.middleware_stack.replace('2nd', mw_replacement)

    assert manager.middlewares == (mw1, mw_replacement, mw3)

    manager.middleware_stack.remove('2nd')

    assert manager.middlewares == (mw1, mw3)


@pytest.mark.skipif(sys.version_info.major < 3, reason="replace requires Py 3")
def test_replace_middleware_without_name(middleware_factory):
    mw1 = middleware_factory()
    mw2 = middleware_factory()
    mw3 = middleware_factory()

    manager = RequestManager(None, BaseProvider(), middlewares=[mw1, mw2, mw3])

    assert manager.middlewares == (mw1, mw2, mw3)

    mw_replacement = middleware_factory()
    manager.middleware_stack.replace(mw2, mw_replacement)

    assert manager.middlewares == (mw1, mw_replacement, mw3)

    manager.middleware_stack.remove(mw_replacement)

    assert manager.middlewares == (mw1, mw3)


def test_remove_middleware(middleware_factory):
    mw1 = middleware_factory()
    mw2 = middleware_factory()
    mw3 = middleware_factory()

    manager = RequestManager(None, BaseProvider(), middlewares=[mw1, mw2, mw3])

    assert manager.middlewares == (mw1, mw2, mw3)

    manager.middleware_stack.remove(mw2)

    assert manager.middlewares == (mw1, mw3)
