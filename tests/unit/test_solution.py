from uuid import uuid4

import pytest

from phoenix_sales.domain.solution import (
    Solution,
    SolutionComponent,
    SolutionComponentType,
    SolutionStatus,
)


def make_solution() -> Solution:
    return Solution(
        tenant_id="tenant-1",
        opportunity_id=uuid4(),
        name="Recommended fixing solution",
        requirement="Secure the specified application",
        application="Structural fixing",
    )


def make_component() -> SolutionComponent:
    return SolutionComponent(
        component_type=SolutionComponentType.PRODUCT,
        item_id="item-1",
        description="Primary solution component",
        quantity=10,
    )


def test_solution_requires_core_identity_and_context():
    solution = make_solution()
    assert solution.version == 1
    assert solution.status is SolutionStatus.DRAFT
    assert solution.opportunity_id is not None


@pytest.mark.parametrize("field", ["tenant_id", "name", "requirement", "application"])
def test_solution_requires_text_fields(field):
    values = {
        "tenant_id": "tenant-1",
        "opportunity_id": uuid4(),
        "name": "Solution",
        "requirement": "Requirement",
        "application": "Application",
    }
    values[field] = ""
    with pytest.raises(ValueError):
        Solution(**values)


def test_solution_version_must_start_at_one():
    with pytest.raises(ValueError, match="version"):
        Solution(
            tenant_id="tenant-1",
            opportunity_id=uuid4(),
            name="Solution",
            requirement="Requirement",
            application="Application",
            version=0,
        )


def test_component_requires_valid_identity_and_quantity():
    with pytest.raises(ValueError, match="item_id"):
        SolutionComponent(SolutionComponentType.PRODUCT, "", "Product", 1)
    with pytest.raises(ValueError, match="quantity"):
        SolutionComponent(SolutionComponentType.PRODUCT, "item", "Product", 0)


def test_add_component_updates_solution():
    solution = make_solution()
    solution.add_component(make_component())
    assert len(solution.components) == 1
    assert solution.components[0].item_id == "item-1"


def test_submit_requires_component_and_moves_to_review():
    solution = make_solution()
    with pytest.raises(ValueError, match="at least one component"):
        solution.submit_for_review()
    solution.add_component(make_component())
    solution.submit_for_review()
    assert solution.status is SolutionStatus.IN_REVIEW


def test_approve_requires_review():
    solution = make_solution()
    with pytest.raises(ValueError, match="in review"):
        solution.approve()
    solution.add_component(make_component())
    solution.submit_for_review()
    solution.approve()
    assert solution.status is SolutionStatus.APPROVED
    assert solution.is_locked


def test_locked_solution_cannot_be_changed():
    solution = make_solution()
    solution.add_component(make_component())
    solution.submit_for_review()
    solution.approve()
    with pytest.raises(ValueError, match="locked"):
        solution.add_component(make_component())


def test_cancel_closes_draft_solution():
    solution = make_solution()
    solution.cancel()
    assert solution.status is SolutionStatus.CANCELLED
    assert solution.is_locked


def test_cancelled_solution_cannot_be_cancelled_again():
    solution = make_solution()
    solution.cancel()
    with pytest.raises(ValueError, match="already closed"):
        solution.cancel()
