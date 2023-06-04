import {LogEvent} from "../model/Events";
import {ResolveEventItem} from "./ResolveEventItem";
import {FixedSizeList} from 'react-window';
import Box from '@mui/material/Box';
import React, {useEffect, useState} from "react";
import Grid from "@mui/material/Grid";

export function EventList({events}: { events: LogEvent[] }) {
    const [width, setWidth] = useState(0);
    const [height, setHeight] = useState(0);
    const [domainLists, setDomainLists] = useState<string[]>([]);

    useEffect(() => {
        const handleResize = () => {
            setWidth(Math.min(800, window.innerWidth));
            setHeight(window.innerHeight - 40);
        }
        window.addEventListener('resize', handleResize);
        handleResize();

        fetch('/api/domain-lists')
            .then(response => response.json())
            .then(list => setDomainLists(list));

        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <>
            <ListHeader></ListHeader>
            <Box
                sx={{
                    width: width,
                    height: height,
                    maxWidth: 800,
                    bgcolor: 'background.paper'
                }}
            >
                <FixedSizeList
                    height={height}
                    width={width}
                    itemSize={50}
                    itemCount={events.length}
                    overscanCount={5}
                    itemData={{events, domainLists}}
                >
                    {ResolveEventItem}
                </FixedSizeList>
            </Box>
        </>
    );
}

function ListHeader() {
    return (
        <Grid container>
            <Grid xs={6} item={true}>
                Domain
            </Grid>
            <Grid xs={3} item={true}>
                Client
            </Grid>
            <Grid xs={3}>Domain list</Grid>
        </Grid>
    );
}
