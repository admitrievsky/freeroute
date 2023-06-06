import {EventType, LogEvent, ResolveEvent} from "./Events";
import {createContext, Dispatch, ReactNode, useReducer} from "react";

interface EventListState {
    events: LogEvent[];
    filteredEvents: LogEvent[];
    clients: string[];
    filterClient: string;
}

export enum EventListActionType {
    addResolveEvent,
    setFilterClient
}

export interface EventListAction {
    type: EventListActionType;
    event?: LogEvent;
    client?: string;
}

// @ts-ignore
export const EventListContext = createContext<EventListState>(null);
export const EventListDispatchContext =
    createContext<Dispatch<EventListAction> | null>(null);


export function EventListProvider({children}: { children: ReactNode }) {
    const [events, dispatch] = useReducer(
        eventListReducer,
        initialEventListState
    );

    return (
        <EventListContext.Provider value={events}>
            <EventListDispatchContext.Provider value={dispatch}>
                {children}
            </EventListDispatchContext.Provider>
        </EventListContext.Provider>
    );
}


function eventListReducer(state: EventListState, action: EventListAction) {
    switch (action.type) {
        case EventListActionType.addResolveEvent: {
            let found = false;
            const clients = new Set<string>();
            const newEvent = action.event as ResolveEvent;
            let newEvents = state.events.map(e => {
                if (e.type === EventType.resolve) {
                    const event = e as ResolveEvent;
                    clients.add(event.remote);
                    if (event.domain === newEvent.domain) {
                        found = true;
                        return newEvent;
                    }
                }
                return e;
            });
            if (!found)
                newEvents.push(newEvent);
            return {
                ...state,
                events: newEvents,
                filteredEvents: filterEvents(newEvents, state.filterClient),
                clients: Array.from(clients)
            }
        }
        case EventListActionType.setFilterClient: {
            return {
                ...state,
                filterClient: action.client as string,
                filteredEvents: filterEvents(state.events, action.client as string),
            }
        }
        default:
            throw new Error(`Unhandled action type: ${action.type}`);
    }
}

function filterEvents(events: LogEvent[], filterClient: string) {
    return events.filter(e => {
        if (e.type !== EventType.resolve)
            return true;
        return filterClient === "" ||
            (e as ResolveEvent).remote === filterClient;
    })
}

const initialEventListState: EventListState = {
    events: [],
    filteredEvents: [],
    clients: [],
    filterClient: ""
}
