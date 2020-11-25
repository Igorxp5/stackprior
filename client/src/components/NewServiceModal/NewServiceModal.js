import React, { Component, Fragment } from "react";

import axios from 'axios';

class NewServiceModal extends Component {

  constructor(props) {
    super(props)
    this.state = {
      selectedPriority: '1',
      selectedStrategy: '',
      name: '',
      endpoint: '',
      server: '',
      port: '',
      by_priority: ''
    }

    this.handleSubmit = this.handleSubmit.bind(this);
  }

  handleChange(event){
    this.setState({
        [event.target.name]: event.target.value
    })

  }

  renderPrioritySelector() {
    return (
      <div>
        <form onSubmit={this.handleSubmit}>
          <input placeholder="NAME" name="name" onChange={(e) => this.setState({ name: e.target.value })} required/>
          <input placeholder="ENDPOINT" name="endpoint" onChange={(e) => this.setState({ endpoint: e.target.value })} required/>
          <select placeholder="PRIORITY"
            onChange={(e) => this.setState({ selectedPriority: e.target.value })}>
            <option disabled>PRIORITY</option>
            <option>1</option>
            <option>2</option>
            <option>3</option>
          </select>
          <select placeholder="STRATEGY"
            onChange={(e) => this.setState({ selectedStrategy: e.target.value })}>
            <option>STRATEGY</option>
            <option>DNS</option>
            <option >ROUND-ROBIN</option>
            <option>BY PRIORITY</option>
          </select>
          <button type="submit">create</button>
        </form>
      </div>
    );
  }

  strategySelected(selectedType){
    if (selectedType === "STRATEGY")
      return ;
    if (selectedType === "DNS")
      return (
        <form>
          <input placeholder="DNS SERVER" onChange={(e) => this.setState({ server: e.target.value })} />
        </form>
      );
    if (selectedType === "ROUND-ROBIN")
      return (
        <form>
          <input placeholder="SERVER" onChange={(e) => this.setState({ server: e.target.value })} />
          <input placeholder="PORT" onChange={(e) => this.setState({ port: e.target.value })} />
        </form>
      );
    if (selectedType === "BY PRIORITY")
      return (
        <form>
          <input placeholder="SERVER" onChange={(e) => this.setState({ server: e.target.value })} />
          <input placeholder="PORT" onChange={(e) => this.setState({ port: e.target.value })} />
          <input placeholder="PRIORITY" onChange={(e) => this.setState({ by_priority: e.target.value })} />
        </form>
      );  
  }

  handleSubmit(event) {
    const {name, endpoint, selectedPriority, selectedStrategy, server, port, by_priority} = this.state;
    console.log(selectedStrategy)
    if (selectedStrategy === '') {
      {console.log("STRATEGY NOT SELECTED, TRY AGAIN")}
    }
    if (selectedStrategy === "DNS") {
      axios.post('http://localhost:3333/services', { //to be defined
        name: name,
        endpoint: endpoint,
        selectedPriority: selectedPriority,
        selectedStrategy: selectedStrategy,
        server: server
      }).then( response => console.log("response", response.data))
    } else if (selectedStrategy === "ROUND-ROBIN") {
      axios.post('http://localhost:3333/services', { //to be defined
        name: name,
        endpoint: endpoint,
        selectedPriority: selectedPriority,
        selectedStrategy: selectedStrategy,
        server: server,
        port: port
      }).then( response => console.log("response", response.data))
    } else if (selectedStrategy === "BY PRIORITY") {
      axios.post('http://localhost:3333/services', { //to be defined
        name: name,
        endpoint: endpoint,
        selectedPriority: selectedPriority,
        selectedStrategy: selectedStrategy,
        server: server,
        port: port,
        by_priority: by_priority
      }).then( response => console.log("response", response.data))
    }
  }

  render(){
    return (
      <Fragment>
        <section >
          {this.renderPrioritySelector()}
          <div>
            {this.strategySelected(this.state.selectedStrategy)}
          </div>
        </section>
      </Fragment>
    );
  }

}

export default NewServiceModal;