import React from 'react';

import './Service.scss';

import ServiceModal from '../ServiceModal/ServiceModal';


const ServicesCard = ({service}) => {

  const printTest = () =>{
    <ServiceModal>test</ServiceModal>
  }

  
  return(
    <div className="card-item">
      <h2 className="card-item__name">{service.name}</h2>
      <p className="card-item__endpoint">{service.endpoint}</p>
      <div className="priority">
        <small>{service.priority}</small>
      </div>
      <button onClick={printTest}> clique</button >
    </div>
  )
}

export default ServicesCard;