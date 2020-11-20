import React from "react";

import axios from 'axios';

import Services from '../components/Services/Services';
import '../';


class Items extends React.Component{

  constructor(props) {
    super(props);

    this.state = {
      services: []
    };

  }

  componentDidMount() {
    this.getServices();
    console.log(this.state);
    
  }

  getServices() {
    axios.get("http://localhost:3333/services")
    .then(response => { 
      const services = response.data;
      this.setState({ services });
    })
  }
  
  render() {
    return(
      <div>
        {this.state.services.map(service => 
        <Services service={service} key={service.name} />)}
      </div>
    )
  }
}


export default Items;