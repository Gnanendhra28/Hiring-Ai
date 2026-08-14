import pytest
import uuid
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.events.memory import InMemoryEventBus

@pytest.mark.asyncio
async def test_event_envelope_json_serialization():
    org_id = uuid.uuid4()
    agg_id = uuid.uuid4()

    event = EventEnvelope(
        event_type="application.created",
        aggregate_id=agg_id,
        organization_id=org_id,
        correlation_id="trace_12345",
        payload={"candidate_name": "Test Candidate", "source": "OUR_PORTAL"}
    )

    json_data = event.to_json()
    assert "application.created" in json_data
    assert str(org_id) in json_data

    deserialized = EventEnvelope.from_json(json_data)
    assert deserialized.event_id == event.event_id
    assert deserialized.aggregate_id == agg_id
    assert deserialized.organization_id == org_id
    assert deserialized.payload["candidate_name"] == "Test Candidate"

@pytest.mark.asyncio
async def test_in_memory_event_bus_publish_subscribe():
    bus = InMemoryEventBus()
    received_events = []

    async def sample_handler(event: EventEnvelope) -> None:
        received_events.append(event)

    bus.subscribe("job.created", sample_handler)

    org_id = uuid.uuid4()
    event = EventEnvelope(
        event_type="job.created",
        aggregate_id=uuid.uuid4(),
        organization_id=org_id,
        correlation_id="corr_999",
        payload={"job_title": "Senior AI Engineer"}
    )

    await bus.publish(event)

    assert len(received_events) == 1
    assert received_events[0].event_type == "job.created"
    assert received_events[0].organization_id == org_id
    assert len(bus.published_events) == 1
