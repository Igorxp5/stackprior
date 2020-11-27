import React from 'react';
import {NavLink} from 'react-router-dom';

import './Header.scss';

const Header = () => {

    return (
        <nav className="navbar">
            <div className="container">
                <NavLink className="logo" to="/">StackPrior</NavLink>
            </div>
        </nav>
    );
};

export default Header;