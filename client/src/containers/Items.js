import React, {Component} from "react";

import axios from 'axios';

import Services from '../components/Services/Services';
import '../';


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
 
  render() {
    return(
      <div>
        <div>
          <button onClick={() => this.orderBy("asc")}>ordenado</button>
          <button onClick={() => this.orderBy("prior")}>prioridade</button>
        </div>
        <div>
          {this.state.services.map(service => 
          <Services service={service} key={service.name} />)}
        </div>
      </div>
    )
  }
}


export default Items;