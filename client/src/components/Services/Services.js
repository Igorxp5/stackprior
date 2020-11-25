import React, {useState} from 'react';

import './Service.scss';

import ServiceModal from '../ServiceModal/ServiceModal';


const ServicesCard = ({service}) => {

  const [isModalVisible, setIsModalVisible] = useState(false);

  
  return(
    <div className="card-item" onClick={() => setIsModalVisible(true) }>
      {isModalVisible ? ( 
            <ServiceModal service={service} key={service.endpoint}
             onClose= { () => setIsModalVisible(false)} />
          ) : null}
      <h2 className="card-item__name">{service.name}</h2>
      <p className="card-item__endpoint">{service.endpoint}</p>
      <div className="priority">
        <small>{service.priority}</small>
      </div>
    </div>
    
  )
}

export default ServicesCard;