import React from 'react';

import './ServiceModal.scss';

const ServiceModal = ({ id = 'modal', onClose = () => {}, children }) => {  

  const handleOutsideClick = (e) => {
    if(e.target.id === id) onClose();
  }

		return (  

			<div id={id} className="modal" onClick={handleOutsideClick}>   
			  <div className="container">
          <button className="close" onClick={onClose}>x</button>
          <div className="content">{children}</div>
        </div> 
      </div>  
      
		);  
}  

export default ServiceModal;