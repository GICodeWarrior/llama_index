import inspect
from typing import Union, Any, Optional, List

import pytest

from llama_index.core.workflow.decorators import step
from llama_index.core.workflow.errors import WorkflowValidationError
from llama_index.core.workflow.events import Event, StartEvent, StopEvent
from llama_index.core.workflow.utils import (
    validate_step_signature,
    get_steps_from_class,
    get_steps_from_instance,
    get_param_types,
    get_return_types,
    is_free_function,
)


class TestEvent(Event):
    pass


class AnotherTestEvent(Event):
    pass


def test_validate_step_signature_of_method():
    def f(self, ev: TestEvent):
        pass

    validate_step_signature(f)


def test_validate_step_signature_of_free_function():
    def f(ev: TestEvent):
        pass

    validate_step_signature(f)


def test_validate_step_signature_union():
    def f(ev: Union[TestEvent, AnotherTestEvent]):
        pass

    validate_step_signature(f)


def test_validate_step_signature_union_invalid():
    def f(ev: Union[TestEvent, str]):
        pass

    with pytest.raises(
        WorkflowValidationError,
        match="Step signature parameters must be annotated with an Event type",
    ):
        validate_step_signature(f)


def test_validate_step_signature_no_params():
    def f():
        pass

    with pytest.raises(
        WorkflowValidationError, match="Step signature must have at least one parameter"
    ):
        validate_step_signature(f)


def test_validate_step_signature_no_annotations():
    def f(self, ev):
        pass

    with pytest.raises(
        WorkflowValidationError,
        match="Step signature parameters must be annotated with an Event type",
    ):
        validate_step_signature(f)


def test_validate_step_signature_wrong_annotations():
    def f(self, ev: str):
        pass

    with pytest.raises(
        WorkflowValidationError,
        match="Step signature parameters must be annotated with an Event type",
    ):
        validate_step_signature(f)


def test_validate_step_signature_too_many_params():
    def f1(self, ev: TestEvent, foo: TestEvent):
        pass

    def f2(ev: TestEvent, foo: TestEvent):
        pass

    with pytest.raises(
        WorkflowValidationError,
        match="must contain exactly one parameter of type Event and no other parameters",
    ):
        validate_step_signature(f1)

    with pytest.raises(
        WorkflowValidationError,
        match="must contain exactly one parameter of type Event and no other parameters",
    ):
        validate_step_signature(f2)


def test_get_steps_from():
    class Test:
        @step()
        def start(self, start: StartEvent) -> TestEvent:
            return TestEvent()

        @step()
        def my_method(self, event: TestEvent) -> StopEvent:
            return StopEvent()

        def not_a_step(self):
            pass

    steps = get_steps_from_class(Test)
    assert len(steps)
    assert "my_method" in steps

    steps = get_steps_from_instance(Test())
    assert len(steps)
    assert "my_method" in steps


def test_get_param_types():
    def f(foo: str):
        pass

    sig = inspect.signature(f)
    res = get_param_types(sig.parameters["foo"])
    assert len(res) == 1
    assert res[0] is str


def test_get_param_types_no_annotations():
    def f(foo):
        pass

    sig = inspect.signature(f)
    res = get_param_types(sig.parameters["foo"])
    assert len(res) == 1
    assert res[0] is Any


def test_get_param_types_union():
    def f(foo: Union[str, int]):
        pass

    sig = inspect.signature(f)
    res = get_param_types(sig.parameters["foo"])
    assert len(res) == 2
    assert res == [str, int]


def test_get_return_types():
    def f(foo: int) -> str:
        return ""

    assert get_return_types(f) == [str]


def test_get_return_types_union():
    def f(foo: int) -> Union[str, int]:
        return ""

    assert get_return_types(f) == [str, int]


def test_get_return_types_optional():
    def f(foo: int) -> Optional[str]:
        return ""

    assert get_return_types(f) == [str]


def test_get_return_types_list():
    def f(foo: int) -> List[str]:
        return [""]

    assert get_return_types(f) == [List[str]]


def test_is_free_function():
    assert is_free_function("my_function") is True
    assert is_free_function("MyClass.my_method") is False
    assert is_free_function("some_function.<locals>.my_function") is True
    assert is_free_function("some_function.<locals>.MyClass.my_function") is False