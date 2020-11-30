import React, { Component} from "react";

import axios from 'axios';

import 'bootstrap/dist/css/bootstrap.min.css';
import { Modal, Button, Form, InputGroup } from 'react-bootstrap';

import './ServiceModal.scss';

class ServiceModal extends Component {

  constructor(props) {
    super(props)
    this.state = {
      name: this.props.service.name,
      endpoint: this.props.service.endpoint,
      sub_endpoint: this.props.service['sub-endpoint'],
      priority: this.props.service.priority,
      strategy: this.props.service.strategy,
      servers: this.props.service.servers,
      host: "",
      port: "",
      by_priority: "",
      strategy_temp: ""
    }

    this.renderStrategy = this.renderStrategy.bind(this);
    this.checkStrategy = this.checkStrategy.bind(this);
    this.closeModal = this.closeModal.bind(this);

  }

  checkStrategy() {
    if (this.state.strategy === "ROUND-ROBIN") {
      this.setState({port: this.props.service.port})
    } else if (this.state.strategy === "BY PRIORITY") {
      this.setState({port: this.props.service.port});
      this.setState({by_priority: this.props.service.by_priority})
    }
  }

  renderServiceEdit() {
    return (
        <Form onSubmit={this.handleSubmit}>
          <InputGroup className="input">
            <Form.Control value={this.state.name} name="name" onChange={(e) => this.setState({ name: e.target.value })} required/>
          </InputGroup>
          <InputGroup className="input">
            <Form.Control value={this.state.endpoint} name="endpoint" onChange={(e) => this.setState({ endpoint: e.target.value })} required/>
          </InputGroup>
          <InputGroup className="input">
            <Form.Control value={this.state.sub_endpoint} name="sub_endpoint" onChange={(e) => this.setState({ sub_endpoint: e.target.value })} required/>
          </InputGroup>
          <InputGroup className="input">
            <Form.Control value={this.state.priority} name="priority" onChange={(e) => this.setState({ priority: e.target.value })} required/>
          </InputGroup>
          <InputGroup className="input">
            <Form.Control as="select" custom defaultValue={this.state.strategy}
              onChange={(e) => this.setState({ temp: e.target.value })}>
              <option disabled>STRATEGY</option>
              {/* <option>DNS</option> */}
              <option>ROUND-ROBIN</option>
              {/* <option>BY PRIORITY</option> */}
            </Form.Control>
            <InputGroup>
              {this.checkQnt()}
              <Form.Control placeholder={""}/>
              <Form.Control placeholder={""}/>
            </InputGroup>
          </InputGroup>
          <button className="submit-button"type="submit">Edit</button>
        </Form>
    );
  }

  checkQnt() {
    var count = 0
      if (this.state.strategy_temp === "") {
        return (
          this.state.servers.map((server) =>
        this.renderStrategy(server, count++))
        )
      }
  }
//   
  checkChange() {
    if (this.state.strategy_temp === "") {
      console.log("test")
      return false;
    } else if (this.state.strategy_temp !== "") {
        return true;
    }
  }

  renderStrategy(server, i) {
    if (this.state.strategy  === "DNS") {
      return(
        <Form className="server-form">
          {console.log("test")}
          <Form.Control className="input-new" placeholder={server.host} onChange={(e) => this.setState({ host: e.target.value })} required/>
        </Form>
      )
    }
    else if (this.state.strategy === "ROUND-ROBIN") {
      return(
        <Form className="server-form">
          <Form.Control />
        </Form>
      )
    } else if (this.state.strategy === "BY PRIORITY" ) {
      return (
        <Form className="server-form">
          <Form.Control className="input-new" value={this.state.server} onChange={(e) => this.setState({ server: e.target.value })} required/>
          <Form.Control className="input-new" placeholder="BY PRIORITY" value={this.state.by_priority} onChange={(e) => this.setState({ by_priority: e.target.value })} required/>
        </Form>
      );
    }
  }

  componentDidMount() {
    this.state.strategy_temp = this.state.strategy;
    this.checkStrategy();

  }

  handleSubmit(event) {
    const {name, endpoint, sub_endpoint, priority, strategy, servers} = this.state;
    if (strategy === "DNS") {
      axios.put('http://localhost:3333/services/', { //to be defined
        name: name,
        endpoint: endpoint,
        sub_endpoint: sub_endpoint,
        priority: priority,
        strategy: strategy,
        servers: servers
      }).then( response => console.log("response", response.data))
    } else if (strategy === "ROUND-ROBIN") {
      axios.put('http://localhost:3333/services', { //to be defined
        name: name,
        endpoint: endpoint,
        sub_endpoint: sub_endpoint,
        priority: priority,
        strategy: strategy,
        servers: servers
      }).then( response => console.log("response", response.data))
    } else if (strategy === "BY PRIORITY") {
      axios.put('http://localhost:3333/services', { //to be defined
        name: name,
        endpoint: endpoint,
        sub_endpoint: sub_endpoint,
        priority: priority,
        strategy: strategy,
        servers: servers
      }).then( response => console.log("response", response.data))
    }
  }

  closeModal() {
    return this.props.callbackParent(false);
  }

  render() {
    return (
      <Modal show={true}
        size="lg"
        aria-labelledby="contained-modal-title-vcenter"
        centered
        >
          <Modal.Header> 
            <Modal.Title  id="contained-modal-title-vcenter">
              <span className="title">NEW SERVICE</span>
            </Modal.Title>
            <Button variant="light" onClick={this.closeModal} > X </Button>
          </Modal.Header>
          
          <section >
            {this.renderServiceEdit()}
            <div>
            </div>
          </section>
        </Modal>
    );
  }

}

export default ServiceModal;