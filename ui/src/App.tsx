import React, {useContext, useEffect} from 'react';
import './App.css';
import {EventType, ResolveEvent} from "./model/Events";
import {
    EventListAction,
    EventListActionType,
    EventListDispatchContext,
    EventListProvider
} from "./model/EventListContext";
import {EventList} from "./components/EventList";

function App() {
    return (
        <div className="App">
            <EventListProvider>
                <AppInner/>
            </EventListProvider>
        </div>
    );
}

function AppInner() {
    const eventDispatch = useContext(EventListDispatchContext);

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
                eventDispatch!({
                    type: EventListActionType.addResolveEvent,
                    event
                } as EventListAction);
            } else {
                console.error(`Failed to resolve ${logEntry}`);
            }
        };

        return () => logEventSource.close();
    }, [eventDispatch]);

    return (
        <EventList/>
    );
}

export default App;
