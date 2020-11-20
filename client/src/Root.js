import React, {Component} from 'react';
import {BrowserRouter, Switch, Route} from 'react-router-dom';

import './Root.css';

import App from './components/App/App';

class Root extends Component {
  render() {
    return (
      <div className="App">
        <BrowserRouter>
            <Switch>
              <Route exact path="/" component={App} />
            </Switch>
        </BrowserRouter>
      </div>
    );
  }
}

export default Root;
