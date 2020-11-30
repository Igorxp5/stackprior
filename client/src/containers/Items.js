import React, {Component} from "react";

import axios from 'axios';

import Services from '../components/Services/Services';
import './Items.scss';

import 'bootstrap/dist/css/bootstrap.min.css';

import { Button, Row } from 'react-bootstrap';

class Items extends Component{

  constructor(props) {
    super(props);

    this.state = {
      services: [],
      order : ""
    };

  }

  orderBy(type) {
    this.setState({order: type });
    this.getServices(type);
  }

  componentDidMount() {
    this.orderBy("asc");
    
  }

  getServices(type) {
    if (type === "prior") {
      axios.get("http://localhost:3333/servicesOrder") // to be defined
    .then(response => { 
      const services = response.data;
      this.setState({ services });
    })
    } else {
      axios.get("http://localhost:3333/services") // to be defined
      .then(response => { 
        const services = response.data;
        this.setState({ services });
      })
    }
  }

  getServicesOrdernate(type) {  // use this function to get the services?
    axios.get("http://localhost:3333/services", {
      params: {
        order_by: this.state.order
      }
    })
    .then( response => console.log("response", response.data))
  }
 
  render() {
    return(
      <div>
        <Row>
          <h5 className="order-title">ORDER BY:</h5>
          <Button className="btn-order" onClick={() => this.orderBy("asc")}>ALPHABETIC</Button>
          <Button className="btn-order" onClick={() => this.orderBy("prior")}>PRIORITY</Button>
        </Row>
        <Row className="cards">
          {this.state.services.map(service => 
          <Services service={service} key={service.name} />)}
        </Row>
      </div>
    )
  }
}


export default Items;