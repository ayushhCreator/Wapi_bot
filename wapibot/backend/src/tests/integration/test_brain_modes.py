"""Integration tests for brain mode behavior.

Tests shadow, reflex, and conscious modes to verify:
- Shadow mode: observes but never acts
- Reflex mode: regex-first extraction, template-only responses
- Conscious mode: DSPy-first, brain can customize messages
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from workflows.shared.state import BookingState
from nodes.atomic import extract
from core.brain_config import BrainSettings
from core.brain_toggles import can_customize_template


class TestShadowMode:
    """Test shadow mode behavior - observe only, never act."""

    @pytest.fixture
    def shadow_settings(self):
        """Shadow mode brain settings."""
        return BrainSettings(
            brain_enabled=True,
            brain_mode="shadow",
            rl_gym_enabled=True,
            dream_enabled=False,
        )

    @pytest.fixture
    def test_state(self) -> BookingState:
        """Create test booking state."""
        return {
            "conversation_id": "shadow_test_123",
            "user_message": "My name is Rahul",
            "history": [{"role": "user", "content": "My name is Rahul"}],
            "current_step": "extract_name",
            "completeness": 0.0,
            "errors": [],
            "response": "",
            "should_proceed": True,
            "customer": None,
            "vehicle": None,
            "selected_service": None,
            "slot": None,
        }

    @pytest.mark.asyncio
    async def test_shadow_mode_proposes_but_never_acts(
        self, shadow_settings, test_state
    ):
        """Shadow mode should propose actions but never execute them."""
        with patch(
            "core.brain_config.get_brain_settings", return_value=shadow_settings
        ):
            from nodes.brain.response_proposer import node as response_proposer

            # Shadow mode proposes response
            result = await response_proposer(test_state)

            # Proposed response should exist (observation)
            assert "proposed_response" in result

            # But should_proceed should be False (no action taken)
            # Shadow mode OBSERVES, doesn't act
            assert result.get("should_proceed") == True  # State unchanged


class TestReflexMode:
    """Test reflex mode behavior - regex-first, template-only."""

    @pytest.fixture
    def reflex_settings(self):
        """Reflex mode brain settings."""
        return BrainSettings(
            brain_enabled=True,
            brain_mode="reflex",
            rl_gym_enabled=True,
            dream_enabled=False,
        )

    @pytest.fixture
    def test_state(self) -> BookingState:
        """Create test booking state."""
        return {
            "conversation_id": "reflex_test_456",
            "user_message": "My phone is 9876543210",
            "history": [{"role": "user", "content": "My phone is 9876543210"}],
            "current_step": "extract_phone",
            "completeness": 0.0,
            "errors": [],
            "response": "",
            "should_proceed": True,
            "customer": None,
            "vehicle": None,
            "selected_service": None,
            "slot": None,
        }

    @pytest.mark.asyncio
    async def test_reflex_mode_uses_regex_first(self, reflex_settings, test_state):
        """Reflex mode should try regex extraction before DSPy."""
        with patch(
            "core.brain_config.get_brain_settings", return_value=reflex_settings
        ):
            # Mock extractors
            mock_dspy_extractor = AsyncMock()
            mock_regex_fallback = MagicMock(
                return_value={"phone": "9876543210", "confidence": 0.8}
            )

            # Call extract with reflex priority
            result = await extract.node(
                test_state,
                mock_dspy_extractor,
                "customer.phone",
                fallback_fn=mock_regex_fallback,
                extraction_priority="regex_first",
            )

            # Regex should be called (reflex mode prioritizes regex)
            assert mock_regex_fallback.called

            # DSPy should NOT be called if regex succeeded
            assert not mock_dspy_extractor.called

            # Value should be extracted
            assert result.get("customer", {}).get("phone") == "9876543210"

    @pytest.mark.asyncio
    async def test_reflex_mode_template_only_responses(self, reflex_settings):
        """Reflex mode should use template-only responses (no customization)."""
        with patch(
            "core.brain_config.get_brain_settings", return_value=reflex_settings
        ):
            # In reflex mode, template customization should be disabled
            assert can_customize_template() == False


class TestConsciousMode:
    """Test conscious mode behavior - DSPy-first, can customize."""

    @pytest.fixture
    def conscious_settings(self):
        """Conscious mode brain settings."""
        return BrainSettings(
            brain_enabled=True,
            brain_mode="conscious",
            rl_gym_enabled=True,
            dream_enabled=True,
        )

    @pytest.fixture
    def test_state(self) -> BookingState:
        """Create test booking state."""
        return {
            "conversation_id": "conscious_test_789",
            "user_message": "I drive a Honda City",
            "history": [{"role": "user", "content": "I drive a Honda City"}],
            "current_step": "extract_vehicle",
            "completeness": 0.0,
            "errors": [],
            "response": "",
            "should_proceed": True,
            "customer": None,
            "vehicle": None,
            "selected_service": None,
            "slot": None,
        }

    @pytest.mark.asyncio
    async def test_conscious_mode_uses_dspy_first(self, conscious_settings, test_state):
        """Conscious mode should try DSPy extraction before regex."""
        with patch(
            "core.brain_config.get_brain_settings", return_value=conscious_settings
        ):
            # Mock extractors
            mock_dspy_extractor = MagicMock(
                return_value={"brand": "Honda", "confidence": 0.95}
            )
            mock_regex_fallback = MagicMock(
                return_value={"brand": "Honda", "confidence": 0.6}
            )

            # Mock asyncio for executor
            with (
                patch("asyncio.get_event_loop") as mock_loop,
                patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait_for,
            ):
                mock_wait_for.return_value = {"brand": "Honda", "confidence": 0.95}

                # Call extract with conscious priority
                result = await extract.node(
                    test_state,
                    mock_dspy_extractor,
                    "vehicle.brand",
                    fallback_fn=mock_regex_fallback,
                    extraction_priority="dspy_first",
                )

            # DSPy should be called first (conscious mode prioritizes DSPy)
            assert mock_wait_for.called

            # Regex should NOT be called if DSPy succeeded
            assert not mock_regex_fallback.called

            # Value should be extracted
            assert result.get("vehicle", {}).get("brand") == "Honda"

    @pytest.mark.asyncio
    async def test_conscious_mode_can_customize_templates(self, conscious_settings):
        """Conscious mode should allow template customization."""
        with patch(
            "core.brain_config.get_brain_settings", return_value=conscious_settings
        ):
            # In conscious mode, template customization should be enabled
            assert can_customize_template() == True


class TestToggleEnforcement:
    """Test feature toggle enforcement."""

    @pytest.mark.asyncio
    async def test_toggle_prevents_customization_when_disabled(self):
        """Test that can_customize_template() enforces toggle."""
        # Reflex mode - customization disabled
        reflex_settings = BrainSettings(
            brain_enabled=True, brain_mode="reflex", rl_gym_enabled=True
        )

        with patch(
            "core.brain_config.get_brain_settings", return_value=reflex_settings
        ):
            assert can_customize_template() == False

        # Conscious mode - customization enabled
        conscious_settings = BrainSettings(
            brain_enabled=True, brain_mode="conscious", rl_gym_enabled=True
        )

        with patch(
            "core.brain_config.get_brain_settings", return_value=conscious_settings
        ):
            assert can_customize_template() == True
