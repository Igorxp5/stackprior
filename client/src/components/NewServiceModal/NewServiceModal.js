import React, { Component } from "react";

import axios from 'axios';

import 'bootstrap/dist/css/bootstrap.min.css';
import { Modal, Form, InputGroup, FormControl, Button } from 'react-bootstrap';

import './NewServiceModal.scss';

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
    this.closeModal = this.closeModal.bind(this);
  }

  handleChange(event){
    this.setState({
        [event.target.name]: event.target.value
    })

  }

  renderPrioritySelector() {
    return (
      <div>
        <Form onSubmit={this.handleSubmit}>
          <InputGroup className="input">
            <Form.Control placeholder="SERVICE NAME" name="name" type="name" onChange={(e) => this.setState({ name: e.target.value })} required/>
          </InputGroup>
          <InputGroup className="input"> 
            <InputGroup.Text>/</InputGroup.Text>
            <FormControl id="inlineFormInputGroup" placeholder="ENDPOINT" name="endpoint" onChange={(e) => this.setState({ endpoint: e.target.value })} required />
          </InputGroup>
          <InputGroup className="input">
            <Form.Control as="select" custom
              onChange={(e) => this.setState({ selectedPriority: e.target.value })}>
              <option disabled>PRIORITY</option>
              <option>1</option>
              <option>2</option>
              <option>3</option>
            </Form.Control>
          </InputGroup>
          <InputGroup className="input">
            <Form.Control as="select" custom
              onChange={(e) => this.setState({ selectedStrategy: e.target.value })}>
              <option>STRATEGY</option>
              <option>DNS</option>
              <option >ROUND-ROBIN</option>
              <option>BY PRIORITY</option>
            </Form.Control>
            <InputGroup>
              {this.strategySelected(this.state.selectedStrategy)}
            </InputGroup>
          </InputGroup>
          <Button className="submit-button"type="submit">CREATE</Button>
        </Form>
      </div>
    );
  }

  strategySelected(selectedType){
    if (selectedType === "STRATEGY")
      return ;
    if (selectedType === "DNS")
      return (
        <FormControl className="input-new" id="inlineFormInputGroup" placeholder="DNS SERVER" onChange={(e) => this.setState({ server: e.target.value })} required/>
      );
    if (selectedType === "ROUND-ROBIN")
      return (
        <Form className="server-form">
          <FormControl className="input-new" id="inlineFormInputGroup" placeholder="SERVER" onChange={(e) => this.setState({ server: e.target.value })} required/>
          <FormControl className="input-new" id="inlineFormInputGroup" placeholder="PORT" onChange={(e) => this.setState({ port: e.target.value })} required/>
        </Form>
      );
    if (selectedType === "BY PRIORITY")
      return (
        <Form className="server-form">
          <FormControl className="input-new" id="inlineFormInputGroup" placeholder="SERVER" onChange={(e) => this.setState({ server: e.target.value })} required/>
          <FormControl className="input-new" id="inlineFormInputGroup" placeholder="PORT" onChange={(e) => this.setState({ port: e.target.value })} required/>
          <FormControl className="input-new" id="inlineFormInputGroup" placeholder="PRIORITY" onChange={(e) => this.setState({ by_priority: e.target.value })} required/>
        </Form>
      );  
  }

  handleSubmit(event) {
    const {name, endpoint, selectedPriority, selectedStrategy, server, port, by_priority} = this.state;
    if (selectedStrategy === '') {
      {alert("STRATEGY NOT SELECTED, TRY AGAIN")}
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

  closeModal() {
    return this.props.callbackParent(false)
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
            {this.renderPrioritySelector()}
          </section>
        </Modal>
    );
  }}

export default NewServiceModal;