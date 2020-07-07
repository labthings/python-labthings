from labthings import event


def test_event():
    e = event.Event("eventName")
    event_data = {"key": "value"}

    response = e.emit(event_data)
    assert response.get("messageType") == "event"
    assert response.get("data") == {"eventName": event_data}
    assert response in e.events


def test_property_status_event():
    e = event.PropertyStatusEvent("propertyName")
    event_data = {"key": "value"}

    response = e.emit(event_data)
    assert response.get("messageType") == "propertyStatus"
    assert response.get("data") == {"propertyName": event_data}


def test_action_status_event():
    e = event.ActionStatusEvent("actionName")
    event_data = {"key": "value"}

    response = e.emit(event_data)
    assert response.get("messageType") == "actionStatus"
    assert response.get("data") == {"actionName": event_data}
