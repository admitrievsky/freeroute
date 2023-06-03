export enum EventType {
    resolve = 'resolve'
}

export interface LogEvent {
    type: EventType;
}

export interface ResolveEvent extends LogEvent {
    type: EventType.resolve;
    remote: string;
    domain: string;
    ips: string[];
    domainList: string | null;
}
