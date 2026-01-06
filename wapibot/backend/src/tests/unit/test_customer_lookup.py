"""Unit test to prove customer lookup works with phone normalization."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from workflows.existing_user_booking import (
    check_customer_exists,
    lookup_customer_node,
)
from workflows.shared.state import BookingState


@pytest.mark.asyncio
async def test_phone_normalization_and_customer_lookup():
    """Test that phone number is normalized and customer is found.

    Scenario: WhatsApp sends 916290818033 (with 91 prefix)
    Expected: Normalizes to 6290818033 and finds existing customer
    """
    # Mock state with WhatsApp number (includes 91 prefix)
    state: BookingState = {
        "conversation_id": "916290818033",
        "user_message": "I want to book a service",
        "history": [],
        "response": "",
        "should_confirm": False,
        "current_step": "lookup_customer",
        "completeness": 0.0,
        "errors": [],
    }

    # Mock YawlitClient response for existing customer
    mock_customer_data = {
        "exists": True,
        "data": {
            "customer_uuid": "CUST-2025-001",
            "first_name": "Hrijul",
            "last_name": "Dey",
            "enabled": 1,
        },
    }

    # Mock the YawlitClient.customer_lookup.check_customer_exists method
    with patch("workflows.existing_user_booking.get_yawlit_client") as mock_client:
        # Setup mock
        mock_lookup = AsyncMock(return_value=mock_customer_data)
        mock_client.return_value.customer_lookup.check_customer_exists = mock_lookup

        # Execute lookup node
        result_state = await lookup_customer_node(state)

        # PROOF 1: Phone number was normalized (91 prefix removed)
        # The mock should be called with normalized phone number
        mock_lookup.assert_called_once_with(identifier="6290818033")
        print("✅ PROOF 1: Phone normalized from 916290818033 → 6290818033")

        # PROOF 2: Customer lookup response stored correctly
        assert "customer_lookup_response" in result_state
        assert result_state["customer_lookup_response"]["exists"] is True
        print("✅ PROOF 2: Customer lookup found existing customer")

        # PROOF 3: Customer data extracted correctly
        assert (
            result_state["customer_lookup_response"]["data"]["first_name"] == "Hrijul"
        )
        assert result_state["customer_lookup_response"]["data"]["last_name"] == "Dey"
        assert (
            result_state["customer_lookup_response"]["data"]["customer_uuid"]
            == "CUST-2025-001"
        )
        print("✅ PROOF 3: Customer data extracted: Hrijul Dey (CUST-2025-001)")


@pytest.mark.asyncio
async def test_routing_existing_customer():
    """Test that existing customer is routed correctly."""
    state: BookingState = {
        "conversation_id": "916290818033",
        "user_message": "I want to book a service",
        "history": [],
        "response": "",
        "should_confirm": False,
        "current_step": "check_customer",
        "completeness": 0.0,
        "errors": [],
        "customer_lookup_response": {
            "exists": True,
            "data": {
                "customer_uuid": "CUST-2025-001",
                "first_name": "Hrijul",
                "last_name": "Dey",
                "enabled": 1,
            },
        },
    }

    # Execute routing check
    route = await check_customer_exists(state)

    # PROOF 4: Existing customer routes to "existing_customer"
    assert route == "existing_customer"
    print("✅ PROOF 4: Routing decision: existing_customer")

    # PROOF 5: Customer data stored in state
    assert "customer" in state
    assert state["customer"]["first_name"] == "Hrijul"
    assert state["customer"]["last_name"] == "Dey"
    assert state["customer"]["customer_uuid"] == "CUST-2025-001"
    print("✅ PROOF 5: Customer data stored in state for workflow use")


@pytest.mark.asyncio
async def test_routing_new_customer():
    """Test that new customer is routed to registration."""
    state: BookingState = {
        "conversation_id": "919999999999",
        "user_message": "I want to book a service",
        "history": [],
        "response": "",
        "should_confirm": False,
        "current_step": "check_customer",
        "completeness": 0.0,
        "errors": [],
        "customer_lookup_response": {"exists": False},
    }

    # Execute routing check
    route = await check_customer_exists(state)

    # PROOF 6: New customer routes to "new_customer"
    assert route == "new_customer"
    print("✅ PROOF 6: Routing decision: new_customer (not found)")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CUSTOMER LOOKUP PROOF - Unit Tests")
    print("=" * 60 + "\n")

    # Run tests
    asyncio.run(test_phone_normalization_and_customer_lookup())
    print()
    asyncio.run(test_routing_existing_customer())
    print()
    asyncio.run(test_routing_new_customer())

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)
    print("\nProof Summary:")
    print("1. Phone number normalization works (916290818033 → 6290818033)")
    print("2. YawlitClient.customer_lookup.check_customer_exists is called correctly")
    print("3. Customer data is extracted from response")
    print("4. Existing customers route to 'existing_customer' flow")
    print("5. Customer data is stored in state for workflow")
    print("6. New customers route to 'new_customer' registration flow")
    print("=" * 60 + "\n")
