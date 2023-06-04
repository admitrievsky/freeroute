import {LogEvent, ResolveEvent} from "../model/Events";
import {ListChildComponentProps} from "react-window";
import {ListItem, Tooltip} from "@mui/material";
import Grid from '@mui/material/Grid';
import React from "react";

export function ResolveEventItem(props: ListChildComponentProps) {
    const {index, style} = props;
    const data = props.data as { events: LogEvent[], domainLists: string[] };
    const event = data.events[index] as ResolveEvent;
    const domainLists = data.domainLists;

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
                    {event.remote}
                </Grid>
                <Grid xs={3}>{event.domainList || '---'}</Grid>
            </Grid>
        </ListItem>
    );
}
