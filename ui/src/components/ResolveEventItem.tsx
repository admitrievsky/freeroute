import {ResolveEvent} from "../model/Events";
import {ListChildComponentProps} from "react-window";
import {Link, ListItem, Tooltip} from "@mui/material";
import Grid from '@mui/material/Grid';
import React, {useContext} from "react";
import {
    EventListAction,
    EventListActionType,
    EventListContext,
    EventListDispatchContext
} from "../model/EventListContext";

export function ResolveEventItem(props: ListChildComponentProps) {
    const {index, style} = props;

    const eventsState = useContext(EventListContext);
    const eventDispatch = useContext(EventListDispatchContext);
    const event = eventsState.filteredEvents[index] as ResolveEvent;

    return (
        <ListItem style={style} key={index} component="div">
            <Grid container>
                <Grid xs={6} item={true}>
                    <Tooltip
                        title={event.ips.map(ip => <div key={ip}>{ip}</div>)}>
                        <div
                            style={{wordBreak: 'break-word'}}>{event.domain}</div>
                    </Tooltip>
                </Grid>
                <Grid xs={3} item={true}>
                    <Link component="button" onClick={() => {
                        eventDispatch!({
                            type: EventListActionType.setFilterClient,
                            client: event.remote
                        } as EventListAction);
                    }}>
                        {event.remote}
                    </Link>
                </Grid>
                <Grid xs={3} item={true}>{event.domainList || '---'}</Grid>
            </Grid>
        </ListItem>
    );
}
