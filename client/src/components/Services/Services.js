import React from 'react';

import './Service.scss';

import ServiceModal from '../ServiceModal/ServiceModal';


const ServicesCard = ({service}) => {

  const sendData = () =>{
    <ServiceModal service={service} key={service.endpoint}></ServiceModal>
  }

  
  return(
    <div className="card-item" onClick={sendData}>
      <h2 className="card-item__name">{service.name}</h2>
      <p className="card-item__endpoint">{service.endpoint}</p>
      <div className="priority">
        <small>{service.priority}</small>
      </div>
    </div>
  )
}

export default ServicesCard;