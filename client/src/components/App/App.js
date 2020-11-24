import React, { useState } from 'react';

import Items from '../../containers/Items';
import Header from '../Header/Header';
import NSModal from '../NewServiceModal/NewServiceModal';
import './App.css';

const App = () => {

  const [isModalVisible, setIsModalVisible] = useState(false);


  return(
    <div id="home-page">
      <Header />
      <main>
        <div>
          <h1> Services </h1>
        </div>
        <div className="products-container .col-sm-6">
          <Items />
        </div>
          <button onClick={() => setIsModalVisible(true) }>New Service</button>
          {isModalVisible ? ( 
            <NSModal onClose= { () => setIsModalVisible(false)} />
          ) : null}
      </main>
    </div>
  )
}

export default App;