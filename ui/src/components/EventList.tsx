import {ResolveEventItem} from "./ResolveEventItem";
import {FixedSizeList} from 'react-window';
import Box from '@mui/material/Box';
import React, {useContext, useEffect, useRef, useState} from "react";
import Grid from "@mui/material/Grid";
import {
    FormControl,
    InputLabel,
    MenuItem,
    Paper,
    Select,
    Stack
} from "@mui/material";
import {
    EventListAction,
    EventListActionType,
    EventListContext,
    EventListDispatchContext
} from "../model/EventListContext";
import {DomainListSettingsButton} from "./DomainListSettingsButton";

export function EventList() {
    const eventsState = useContext(EventListContext);
    const {filteredEvents} = eventsState;
    const [width, setWidth] = useState(0);
    const [height, setHeight] = useState(0);
    const listRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleResize = () => {
            setWidth(Math.min(800, window.innerWidth));
            setHeight(window.innerHeight - (listRef.current?.offsetTop || 0));
        }
        window.addEventListener('resize', handleResize);
        handleResize();

        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <>
            <Box
                sx={{
                    width: width,
                    height: height,
                    maxWidth: 800,
                    bgcolor: 'background.paper'
                }}
            >
                <Stack spacing={2} direction="row" justifyContent="flex-end"
                       mb={3}>
                    <DomainListSettingsButton/>
                </Stack>
                <ListHeader></ListHeader>
                <div ref={listRef}>
                    <FixedSizeList
                        height={height}
                        width={width}
                        itemSize={50}
                        itemCount={filteredEvents.length}
                        overscanCount={5}
                    >
                        {ResolveEventItem}
                    </FixedSizeList>
                </div>
            </Box>
        </>
    );
}

function ListHeader() {
    const eventsState = useContext(EventListContext);
    const eventDispatch = useContext(EventListDispatchContext);
    const {clients, filterClient} = eventsState;

    return (
        <Grid container>
            <Grid xs={6} item={true}>
                <Paper className="grid-header-paper">Domain</Paper>
            </Grid>
            <Grid xs={3} item={true}>
                <FormControl sx={{m: 1, minWidth: 120}} size="small">
                    <InputLabel id="demo-select-small-label">Filter</InputLabel>
                    <Select value={filterClient} label="Filter"
                            onChange={event => {
                                eventDispatch!({
                                    type: EventListActionType.setFilterClient,
                                    client: event.target.value as string
                                } as EventListAction);
                            }}>
                        <MenuItem value="" key="">All</MenuItem>
                        {clients.map(client =>
                            <MenuItem value={client}
                                      key={client}>{client}</MenuItem>)}
                    </Select>
                </FormControl>
            </Grid>
            <Grid xs={3} item={true}><Paper className="grid-header-paper">Domain
                list</Paper></Grid>
        </Grid>
    );
}
