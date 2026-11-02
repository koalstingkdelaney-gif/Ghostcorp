"""Calling / SMS adapters — DISABLED by design (brief section 2.5).

Automated marketing calls and texts are regulated (TCPA and provider rules).
A public phone number is NOT consent. This module exists so the interface,
guardrails, and audit trail are ready, but no call or text can be placed
until every prerequisite in docs/PROVIDER_SETUP.md is verifiably complete
and the owner enables it. There is no code path that bypasses this.
"""


class CommsDisabled(Exception):
    pass


PREREQUISITES = [
    "owner completed provider onboarding and business/identity verification",
    "required voice/SMS registrations approved by the provider",
    "documented lawful basis / consent for each recipient",
    "owner-approved call/text scripts on file",
    "calling-hour controls, caller ID, opt-out/STOP handling and suppression lists active",
    "owner has explicitly enabled calling/SMS in configuration",
]


class DisabledCommsProvider:
    name = "disabled"

    def __init__(self, calling_enabled: bool = False, sms_enabled: bool = False):
        self.calling_enabled = calling_enabled
        self.sms_enabled = sms_enabled

    def place_call(self, to_number: str, script_id: str, consent_record: dict | None):
        if not self.calling_enabled:
            raise CommsDisabled(
                "calling is disabled: compliance prerequisites are not all met "
                f"({'; '.join(PREREQUISITES)})"
            )
        if not consent_record:
            raise CommsDisabled("calling refused: no documented consent record for recipient")
        raise CommsDisabled("no live voice provider configured")

    def send_sms(self, to_number: str, body: str, consent_record: dict | None):
        if not self.sms_enabled:
            raise CommsDisabled(
                "SMS is disabled: compliance prerequisites are not all met "
                f"({'; '.join(PREREQUISITES)})"
            )
        if not consent_record:
            raise CommsDisabled("SMS refused: no documented consent record for recipient")
        raise CommsDisabled("no live SMS provider configured")
