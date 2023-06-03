import {EventType, LogEvent, ResolveEvent} from "../model/Events";
import {ResolveEventItem} from "./ResolveEventItem";

export function EventList({events}: { events: LogEvent[] }) {
    return (
        <ul>
            {events.map(event => {
                switch (event.type) {
                    case EventType.resolve: {
                        const e = event as ResolveEvent;
                        return <ResolveEventItem key={e.domain} event={e}/>
                    }
                    default:
                        return <li key={event.type}>Unknown event
                            type: {event.type}</li>
                }
            })}
        </ul>
    );
}
