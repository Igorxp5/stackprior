import React, { Component,} from "react";

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
      priority: this.props.service.priority,
      strategy: this.props.service.strategy,
      server: this.props.service.server,
      port: "",
      by_priority: ""
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
            <Form.Control placeholder={this.state.name} name="name" onChange={(e) => this.setState({ name: e.target.value })} required/>
          </InputGroup>
          <InputGroup className="input">
            <Form.Control placeholder={this.state.endpoint} name="endpoint" onChange={(e) => this.setState({ endpoint: e.target.value })} required/>
          </InputGroup>
          <InputGroup className="input">
            <Form.Control as="select" custom defaultValue={this.state.priority}
              onChange={(e) => this.setState({ priority: e.target.value })}>
              <option disabled>PRIORITY</option>
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
            </Form.Control>
          </InputGroup>
          <InputGroup className="input">
            <Form.Control as="select" custom defaultValue={this.state.strategy}
              onChange={(e) => this.setState({ strategy: e.target.value })}>
              <option disabled>STRATEGY</option>
              <option>DNS</option>
              <option >ROUND-ROBIN</option>
              <option>BY PRIORITY</option>
            </Form.Control>
            <InputGroup>
              {this.renderStrategy(this.state.strategy)}
            </InputGroup>
          </InputGroup>
          <button className="submit-button"type="submit">Edit</button>
        </Form>
    );
  }


  renderStrategy() {
    if (this.state.strategy === "DNS") {
      return(
        <Form.Control className="input-new" placeholder={this.state.server} onChange={(e) => this.setState({ server: e.target.value })} required/>
      )
    } else if (this.state.strategy === "ROUND-ROBIN") {
      return (
        <Form>
          <Form.Control className="input-new" placeholder={this.state.server} onChange={(e) => this.setState({ server: e.target.value })} required/>
          <Form.Control className="input-new" placeholder={this.state.port} onChange={(e) => this.setState({ port: e.target.value })} required/>
        </Form>
      );
    } else if (this.state.strategy === "BY PRIORITY") {
      return (
        <Form>
          <Form.Control className="input-new" placeholder={this.state.server} onChange={(e) => this.setState({ server: e.target.value })} required/>
          <Form.Control className="input-new" placeholder={this.state.port} onChange={(e) => this.setState({ port: e.target.value })} required/>
          <Form.Control className="input-new" placeholder={this.state.by_priority} onChange={(e) => this.setState({ by_priority: e.target.value })} required/>
        </Form>
      );
    }
  }

  componentDidMount() {
    this.checkStrategy();
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

  closeModal() {
    return this.props.callbackParent(false);
  }

  render(){
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