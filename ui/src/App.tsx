import React, {useEffect, useReducer} from 'react';
import './App.css';
import {EventType, ResolveEvent} from "./model/Events";
import {
    EventListAction,
    EventListActionType,
    eventListReducer,
    initialEventListState
} from "./model/EventListReducer";
import {EventList} from "./components/EventList";

function App() {
    const [eventsState, eventDispatch] = useReducer(eventListReducer, initialEventListState);

    useEffect(() => {
        const logEventSource = new EventSource('/api/event-log');
        logEventSource.onmessage = (event) => {
            const logEntry = JSON.parse(event.data);
            if (logEntry.type === EventType.resolve) {
                const event = {
                    type: logEntry.type,
                    remote: logEntry.remote,
                    domain: logEntry.domain,
                    ips: logEntry.ips,
                    domainList: logEntry.domain_list,
                } as ResolveEvent;
                eventDispatch({
                    type: EventListActionType.addResolveEvent,
                    event
                } as EventListAction);
            } else {
                console.error(`Failed to resolve ${logEntry}`);
            }
        };

        return () => logEventSource.close();
    }, []);
    return (
        <div className="App">
            <EventList events={eventsState.events}/>
        </div>
    );
}

export default App;
