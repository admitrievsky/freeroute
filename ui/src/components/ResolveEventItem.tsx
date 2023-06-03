import {ResolveEvent} from "../model/Events";

export function ResolveEventItem({event}: { event: ResolveEvent }) {
    return (
        <li>
            <h3>{event.domain}</h3>
            <p>{event.remote}</p>
            <p>{event.ips.join(', ')}</p>
            <p>{event.domainList}</p>
        </li>
    );
}
