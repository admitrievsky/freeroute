import React, {useEffect, useState} from "react";
import {
    AppBar,
    Dialog,
    Grid,
    IconButton,
    List,
    ListItem,
    ListItemButton,
    ListItemText,
    Slide,
    Snackbar,
    TextField,
    Toolbar,
    Typography
} from "@mui/material";
import {TransitionProps} from '@mui/material/transitions';
import CloseIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/Delete';
import Button from "@mui/material/Button";

const Transition = React.forwardRef(function Transition(
    props: TransitionProps & {
        children: React.ReactElement;
    },
    ref: React.Ref<unknown>,
) {
    return <Slide direction="up" ref={ref} {...props} />;
});

export function EditDomainListDialog(
    {domainList, open, onClose}: {
        domainList: string, open: boolean, onClose: () => void,
    }) {

    const [list, setList] = useState<string[]>([]);
    const [lastDeletedDomain, setLastDeletedDomain] = useState<string>('');

    useEffect(() => {
        if (!domainList || !open) return;
        fetch(`/api/domain-lists/${encodeURIComponent(domainList)}`)
            .then(response => response.json())
            .then(list => setList(list));
    }, [domainList, open]);

    const onDelete = (domain: string) => {
        fetch(`/api/domain-lists/${encodeURIComponent(domainList)}`, {
            method: 'DELETE',
            body: JSON.stringify({domain}),
        }).then(response => {
            if (!response.ok) {
                alert(`Failed to delete domain ${domain}: ${response.statusText}`);
                return;
            }
            setList(list.filter((d) => d !== domain));
            setLastDeletedDomain(domain);
        });
    };

    const addDomain = (domain: string) => {
        if (!domain) return;

        setLastDeletedDomain('');
        fetch(`/api/domain-lists/${encodeURIComponent(domainList)}`, {
            method: 'POST',
            body: JSON.stringify({domain}),
        }).then(response => {
            if (!response.ok) {
                alert(`Failed to add domain ${domain}: ${response.statusText}`);
                return;
            }
            setList([...list, domain].sort((a, b) => +(a > b)));
        });
    }

    const undeleteAction = (
        <React.Fragment>
            <Button color="secondary" size="small"
                    onClick={() => addDomain(lastDeletedDomain)}>
                UNDO
            </Button>
        </React.Fragment>
    );

    return (<>
        <Dialog
            fullScreen
            open={open}
            onClose={onClose}
            TransitionComponent={Transition}
        >
            <AppBar sx={{position: 'relative', marginBottom: 1}}>
                <Toolbar>
                    <IconButton
                        edge="start"
                        color="inherit"
                        onClick={onClose}
                        aria-label="close"
                    >
                        <CloseIcon/>
                    </IconButton>
                    <Typography sx={{ml: 2, flex: 1}} variant="h6"
                                component="div">
                        Edit `{domainList}` Domain List
                    </Typography>
                </Toolbar>
            </AppBar>

            <AddDomainComponent domainList={list} onAdd={addDomain}/>

            <List>{
                list.map((domain) => {
                    return (
                        <ListItem
                            key={domain}
                            secondaryAction={
                                <IconButton edge="end" aria-label="actions"
                                            onClick={() => onDelete(domain)}>
                                    <DeleteIcon/>
                                </IconButton>
                            }
                            disablePadding
                        >
                            <ListItemButton role={undefined} dense>
                                <ListItemText primary={domain}/>
                            </ListItemButton>
                        </ListItem>);
                })}</List>
        </Dialog>
        <Snackbar
            open={lastDeletedDomain !== ''}
            onClose={() => setLastDeletedDomain('')}
            autoHideDuration={6000}
            message={`Domain ${lastDeletedDomain} deleted`}
            action={undeleteAction}
        />
    </>);
}

function AddDomainComponent({domainList, onAdd}: {
    domainList: string[],
    onAdd: (domain: string) => void
}) {
    const [addDomainText, setAddDomainText] = useState<string>('');

    return <Grid container spacing={2}>
        <Grid item xs={8}>
            <TextField label="Add domain" variant="outlined" fullWidth
                       value={addDomainText}
                       onChange={e => setAddDomainText(e.target.value.trim())}/>
        </Grid>
        <Grid item alignItems="stretch" style={{display: "flex"}}>
            <Button variant="contained"
                    onClick={() => {
                        onAdd(addDomainText);
                        setAddDomainText('');
                    }}
                    disabled={!addDomainText || domainList.includes(addDomainText)}>Add</Button>
        </Grid>
    </Grid>
}
