import React, { Component, Fragment} from "react";

import axios from 'axios';

class ServiceModal extends Component {

  constructor(props) {
    super(props)
    this.state = {
      name: this.props.service.name,
      endpoint: this.props.service.endpoint,
      priority: this.props.service.priority,
      strategy: this.props.service.strategy,
      server: this.props.service.server,
      port: "",
      by_priority: ""
    }

    this.renderStrategy = this.renderStrategy.bind(this);
    this.checkStrategy = this.checkStrategy.bind(this);
  }

  checkStrategy() {
    if (this.state.strategy === "ROUND-ROBIN") {
      this.setState({port: this.props.service.port})
      console.log(this.props.service.port)
    } else if (this.state.strategy === "BY PRIORITY") {
      this.setState({port: this.props.service.port});
      this.setState({by_priority: this.props.service.by_priority})
    }
  }

  renderServiceEdit() {
    return (
      <div>
        <form onSubmit={this.handleSubmit}>
          <input placeholder={this.state.name} name="name" onChange={(e) => this.setState({ name: e.target.value })} required/>
          <input placeholder={this.state.endpoint} name="endpoint" onChange={(e) => this.setState({ endpoint: e.target.value })} required/>
          <select defaultValue={this.state.priority}
            onChange={(e) => this.setState({ selectedPriority: e.target.value })}>
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
          </select>
          <div>
            {this.renderStrategy()}
          </div>
          <button type="submit">create</button>
        </form>
      </div>
    );
  }

  renderStrategy() {
    if (this.state.strategy === "DNS") {
      return(
        <input placeholder={this.state.server} onChange={(e) => this.setState({ server: e.target.value })} required/>
      )
    } else if (this.state.strategy === "ROUND-ROBIN") {
      return (
        <form>
          <input placeholder={this.state.server} onChange={(e) => this.setState({ server: e.target.value })} required/>
          <input placeholder={this.state.port} onChange={(e) => this.setState({ port: e.target.value })} required/>
        </form>
      );
    } else if (this.state.strategy === "BY PRIORITY") {
      return (
        <form>
          <input placeholder={this.state.server} onChange={(e) => this.setState({ server: e.target.value })} required/>
          <input placeholder={this.state.port} onChange={(e) => this.setState({ port: e.target.value })} required/>
          <input placeholder={this.state.by_priority} onChange={(e) => this.setState({ by_priority: e.target.value })} required/>
        </form>
      );
    }
  }

  componentDidMount() {
    this.checkStrategy()
    console.log(this.state.name)
    console.log(this.state.priority)
  }

  handleSubmit(event) {
    const {name, endpoint, priority, strategy, server, port, by_priority} = this.state;
    if (strategy === "DNS") {
      axios.put('http://localhost:3333/services/', { //to be defined
        name: name,
        endpoint: endpoint,
        priority: priority,
        strategy: strategy,
        server: server
      }).then( response => console.log("response", response.data))
    } else if (strategy === "ROUND-ROBIN") {
      axios.put('http://localhost:3333/services', { //to be defined
        name: name,
        endpoint: endpoint,
        priority: priority,
        strategy: strategy,
        server: server,
        port: port
      }).then( response => console.log("response", response.data))
    } else if (strategy === "BY PRIORITY") {
      axios.put('http://localhost:3333/services', { //to be defined
        name: name,
        endpoint: endpoint,
        priority: priority,
        strategy: strategy,
        server: server,
        port: port,
        by_priority: by_priority
      }).then( response => console.log("response", response.data))
    }
  }

  render(){
    return (
      <Fragment>
        <div>
          <h1>{this.state.name}</h1>
        <section >
          {this.renderServiceEdit()}
          <div>
          </div>
        </section>
        </div>
      </Fragment>
    );
  }

}

export default ServiceModal;