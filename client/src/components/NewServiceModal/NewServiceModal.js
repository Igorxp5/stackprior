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
      sub_endpoint: '',
      servers: [],
      serverdns: '',
      by_priority: '',
      show: false
    }

    this.handleSubmit = this.handleSubmit.bind(this);
    this.closeModal = this.closeModal.bind(this);
    this.strategySelected = this.strategySelected.bind(this);
  }

  handleChange(event){
    this.setState({
        [event.target.name]: event.target.value
    })

  }

  handleClick(e, type) {
    if (type === "ROUND") {
      const result = this.state.serverdns.split(":")
      this.state.servers.push({"host": result[0], "port": result[1]})
      } 
    else if (type === "PRIORITY") {
      const result = this.state.serverdns.split(":")
      this.state.servers.push({"host": result[0], "port": result[1], "weight": this.state.by_priority})
      }
    alert("Adicionado com sucesso")
  }

  renderPrioritySelector() {
    return (
      <div>
        <Form onSubmit={this.handleSubmit}>
          <InputGroup className="input">
            <Form.Control placeholder="SERVICE NAME" name="name" type="name" onChange={(e) => this.setState({ name: e.target.value })} required/>
          </InputGroup>
          <InputGroup className="input"> 
            <FormControl id="inlineFormInputGroup" placeholder="/ENDPOINT" name="endpoint" onChange={(e) => this.setState({ endpoint: e.target.value })} required />
          </InputGroup>
          <InputGroup className="input"> 
            <FormControl id="inlineFormInputGroup" placeholder="/SUB ENDPOINT" name="endpoint" onChange={(e) => this.setState({ sub_endpoint: e.target.value })} required />
          </InputGroup>
          <InputGroup className="input">
            <FormControl id="inlineFormInputGroup" placeholder="PRIORITY" name="priority" onChange={(e) => this.setState({ selectedPriority: e.target.value })} required />
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

  strategySelected(selectedType) {
    if (selectedType === "DNS")
      return (
        <Form className="server-form">
          <FormControl className="input-new" id="inlineFormInputGroup" placeholder="SERVER" onChange={(e) => this.setState({ serverdns: e.target.value })} required/>
        </Form>
      );
    if (selectedType === "ROUND-ROBIN")
      return (
        <Form className="server-form">
          <FormControl className="input-new" id="inlineFormInputGroup" placeholder="SERVER:PORT" onChange={(e) => this.setState({ serverdns: e.target.value })} required/>
          <Button variant="light" onClick={() => this.handleClick(this.state.selectedStrategy, "ROUND")} > + </Button>
        </Form>
        
      );
    if (selectedType === "BY PRIORITY")
      return (
        <Form className="server-form">
          <FormControl className="input-new" id="inlineFormInputGroup" placeholder="SERVER:PORT" onChange={(e) => this.setState({ serverdns: e.target.value })} required/>
          <FormControl className="input-new" id="inlineFormInputGroup" placeholder="PRIORITY" onChange={(e) => this.setState({ by_priority: e.target.value })} required/>
          <Button variant="light" onClick={() => this.handleClick(this.state.selectedStrategy, "PRIORITY")} > + </Button>
        </Form>
      );  
  }

  handleSubmit(event) {
    if (this.state.serverdns === '') {
      return alert("Server empty, service not created")
    }
    const {name, endpoint, sub_endpoint, selectedPriority, selectedStrategy, servers} = this.state;
    if (selectedStrategy === '') {
      {alert("STRATEGY NOT SELECTED, TRY AGAIN")}
    }
    if (selectedStrategy === "DNS") {
      this.state.servers.push({"host": this.state.serverdns})
      axios.post('http://localhost:3333/services', { //to be defined
        name: name,
        endpoint: endpoint,
        sub_endpoint: sub_endpoint,
        selectedPriority: selectedPriority,
        selectedStrategy: selectedStrategy,
        servers: servers
      }).then( response => console.log("response", response.data))
    } else if (selectedStrategy === "ROUND-ROBIN") {
      axios.post('http://localhost:3333/services', { //to be defined
        name: name,
        endpoint: endpoint,
        sub_endpoint: sub_endpoint,
        selectedPriority: selectedPriority,
        selectedStrategy: selectedStrategy,
        servers: servers
      }).then( response => console.log("response", response.data))
    } else if (selectedStrategy === "BY PRIORITY") {
      axios.post('http://localhost:3333/services', { //to be defined
        name: name,
        endpoint: endpoint,
        sub_endpoint: sub_endpoint,
        selectedPriority: selectedPriority,
        selectedStrategy: selectedStrategy,
        servers: servers
      }).then( response => console.log("response", response.data))
    }
  }

  closeModal() {
    return this.props.callbackParent(false)
  }

  render () {
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