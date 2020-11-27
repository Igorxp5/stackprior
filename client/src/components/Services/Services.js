import React from 'react';

import './Services.scss';

import 'bootstrap/dist/css/bootstrap.min.css';
import { Col } from 'react-bootstrap';

import ServiceModal from '../ServiceModal/ServiceModal';


const ServicesCard = ({service}) => {

  const [modalShow, setModalShow] = React.useState(false);

  
  return(
    <>
      <Col className="card-item" onClick={() => setModalShow(true) }>
        <h2 className="card-item__name">{service.name}</h2>
        <p className="card-item__endpoint">/{service.endpoint}</p>
        <div className="card-item__priority">
          <p>{service.priority}</p>
        </div>
      </Col>
      {modalShow ? ( 
          <ServiceModal service={service} key={service.endpoint} 
            callbackParent={(bool) => setModalShow(bool)}
            show={modalShow}
            onHide={() => setModalShow(false)} />
        ) : null}
    </>
    
  )
}

export default ServicesCard;