import {EventType, LogEvent, ResolveEvent} from "./Events";

interface EventListState {
    events: LogEvent[];
}

export enum EventListActionType {
    addResolveEvent
}

export interface EventListAction {
    type: EventListActionType;
    event: LogEvent;
}

export function eventListReducer(state: EventListState, action: EventListAction) {
    switch (action.type) {
        case EventListActionType.addResolveEvent: {
            let found = false;
            const event = action.event as ResolveEvent;
            let newEvents = state.events.map(e => {
                if (e.type === EventType.resolve &&
                    (e as ResolveEvent).domain === event.domain
                ) {
                    found = true;
                    return action.event;
                }
                return e;
            });
            if (!found)
                newEvents.push(action.event);
            return {
                ...state,
                events: newEvents
            }
        }
        default:
            throw new Error(`Unhandled action type: ${action.type}`);
    }
}

export const initialEventListState: EventListState = {
    events: []
}
