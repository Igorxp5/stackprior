import React, { useState } from 'react';

import Services from '../../containers/Items';
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
          <Services />
        </div>
          <button onClick={() => setIsModalVisible(true) }>clique</button>
          {isModalVisible ? ( 
            <NSModal onClose= { () => setIsModalVisible(false)} />
          ) : null}
      </main>
    </div>
  )
}

export default App;