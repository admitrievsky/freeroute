import * as React from 'react';
import {useEffect, useState} from 'react';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';

export function DomainListSettingsButton() {
    const [domainLists, setDomainLists] = useState<string[]>([]);
    const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);
    const handleClick = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };
    const handleClose = () => {
        setAnchorEl(null);
    };

    useEffect(() => {
        fetch('/api/domain-lists')
            .then(response => response.json())
            .then(list => setDomainLists(list));
    });

    return (<>
        <Button
            onClick={handleClick} variant="contained"
        >
            Edit Domain Lists
        </Button>
        <Menu
            anchorEl={anchorEl}
            open={open}
            onClose={handleClose}
            anchorOrigin={{
                vertical: 'top',
                horizontal: 'left',
            }}
            transformOrigin={{
                vertical: 'top',
                horizontal: 'left',
            }}
        >
            {
                domainLists.map((domainList) => {
                    return <MenuItem key={domainList}
                                     onClick={handleClose}>{domainList}
                    </MenuItem>;
                })
            }
        </Menu>
    </>);
}
